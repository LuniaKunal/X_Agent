# backend/app/services/twitter_service.py
import json
from twikit import Client
from core.config import settings
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import csv
import time
import random
from twikit.errors import TooManyRequests
from service.sentiment_service import analyze_sentiment    # perform_sentiment_analysis_and_store Not using for Now
from utils.helpers import map_sentiment_label
from db import crud
from db.database import get_supabase_client

# Set up basic logging
print("Loading twitter_service.py module")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def load_cookies(filename: str) -> Optional[dict]:
    print(f"[DEBUG] Attempting to load cookies from: {filename}")
    try:
        with open(filename, 'r') as f:
            cookies = json.load(f)
        print(f"[DEBUG] Successfully loaded cookies from {filename}")
        return cookies
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[DEBUG] Error loading cookies: {e}")
        logger.error(f"Error loading cookies from {filename}: {e}")
        return None

async def get_tweets(query: str, count: int) -> List[dict]:
    print(f"[DEBUG] get_tweets called with query='{query}', count={count}")
    client = Client('en-US')

    print(f"[DEBUG] Loading cookies from {settings.TWIKIT_COOKIES_FILE}")
    cookies = await load_cookies(settings.TWIKIT_COOKIES_FILE)
    if not cookies:
        print("[DEBUG] No cookies loaded, returning empty tweet list")
        return []
    print("[DEBUG] Setting cookies to client")
    client.set_cookies(cookies)
    try:
        print(f"[DEBUG] Searching for tweets with query='{query}', count={count}")
        tweets = await client.search_tweet(query, 'Latest', count=count)
        print(f"[DEBUG] Retrieved {len(tweets)} tweets from API")
        
        tweet_data = [get_tweet_data(tweet) for tweet in tweets]
        print(f"[DEBUG] Processed {len(tweet_data)} tweets")
        return tweet_data
    except Exception as e:
        print(f"[DEBUG] An error occurred during tweet retrieval: {e}")
        logger.error(f"Error during tweet retrieval: {e}")
        return []
    
async def get_replies_for_tweet(tweet_id: int) -> List[Dict]:
    """
    Fetches direct replies for a given tweet ID using pagination.
    Adds a random delay between 0-5 seconds to avoid rate limits.
    """
    print(f"[DEBUG] get_replies_for_tweet called for tweet_id={tweet_id}")
    
    try:
        # Fetch replies using pagination
        print(f"[DEBUG] Fetching replies for tweet {tweet_id}")
        replies = await get_replies(str(tweet_id))
        
        if replies:
            print(f"[DEBUG] Found {len(replies)} replies for tweet {tweet_id}")
            reply_texts = [reply.text for reply in replies]
            sentiments = analyze_sentiment(reply_texts)
            
            for reply, sentiment in zip(replies, sentiments):
                reply.sentiment = map_sentiment_label(sentiment['label'])
                reply.score = sentiment['score']
            
            return [get_tweet_data(reply) for reply in replies]
        return []
    except Exception as e:
        print(f"[DEBUG] Error fetching replies for tweet {tweet_id}: {e}")
        logger.error(f"Error fetching replies for tweet {tweet_id}: {e}")
        return []

async def get_replies(tweet_id: str, count: int = 100) -> list:
    """
    Fetch up to `count` replies for a given tweet_id using pagination.
    """
    print(f"[DEBUG] get_replies called for tweet_id={tweet_id}")
    client = Client('en-US')
    all_replies = []
    cursor = ""

    try:
        # Load cookies
        cookies = await load_cookies(settings.TWIKIT_COOKIES_FILE)
        if not cookies:
            print("[DEBUG] No cookies loaded for reply fetching")
            return []

        client.set_cookies(cookies)

        while len(all_replies) < count:
            print(f"[DEBUG] Fetching replies batch with cursor: {cursor}")
            try:
                result = await client._get_more_replies(tweet_id, cursor)
                if len(result) == 1:
                    break
            except TooManyRequests as e:
                # rate_limit_reset = datetime.fromtimestamp(e.rate_limit_reset)
                print(f"[DEBUG] Rate limit exceeded. Resetting at {datetime.now()}")
                # wait_time = (rate_limit_reset - datetime.now()).total_seconds()
                time.sleep(100)
                continue
            
            if not hasattr(result, '_Result__results') or not result._Result__results:
                break

            all_replies.extend(result._Result__results)
            print(f"[DEBUG] Added {len(result._Result__results)} replies, total: {len(all_replies)}")

            if not hasattr(result, 'next_cursor'):
                break

            cursor = result.next_cursor

        return all_replies

    except Exception as e:
        print(f"[DEBUG] Error in get_replies: {e}")
        logger.error(f"Error in get_replies: {e}")
        return []

def get_tweet_data(tweet) -> Dict:
    """Enhanced tweet data formatting with additional metrics"""
    try:
        legacy_data = tweet._legacy if hasattr(tweet, '_legacy') else {}
        core_data = tweet._data.get('core', {}) if hasattr(tweet, '_data') else {}
        user_data = core_data.get('user_results', {}).get('result', {}).get('legacy', {})

        text = legacy_data.get('full_text', '')
        # Analyze sentiment for each tweet
        sentiment_results = analyze_sentiment([text])
        sentiment = sentiment_results[0] if sentiment_results else {}

        return {
            'id': getattr(tweet, 'id', ''),
            'text': text,
            'username': user_data.get('screen_name', 'unknown'),
            'created_at': legacy_data.get('created_at', ''),
            'likes': legacy_data.get('favorite_count', 0),
            'replies': legacy_data.get('reply_count', 0),
            'retweets': legacy_data.get('retweet_count', 0),
            'quote_count': legacy_data.get('quote_count', 0),
            'sentiment': sentiment.get('label', 'neutral'),
            'score': float(sentiment.get('score', 0.0))
        }
    except Exception as e:
        print(f"[DEBUG] Error processing tweet data: {e}")
        logger.error(f"Error processing tweet data: {e}")
        return {'error': str(e)}

async def fetch_user_tweets_and_replies(username: str, max_tweets: int, supabase: Client):
    """
    Fetch tweets and replies for a specific user.
    Uses the .next function to retrieve more tweets and adds random delays to avoid rate limits.

    returns: CSV file with tweets and replies
    """
    print(f"[DEBUG] fetch_user_tweets_and_replies called for username='{username}', max_tweets={max_tweets}")
    client = Client('en-US')
    
    # Load cookies
    print(f"[DEBUG] Loading cookies from {settings.TWIKIT_COOKIES_FILE}")
    cookies = await load_cookies(settings.TWIKIT_COOKIES_FILE)
    if not cookies:
        print(f"[DEBUG] No cookies loaded for user {username}")
        return None
    print(f"[DEBUG] Setting cookies to client for user {username}")
    client.set_cookies(cookies)
    
    try:
        # Get user object by username
        print(f"[DEBUG] Getting user by screen name: {username}")
        user = await client.get_user_by_screen_name(username)
        if not user:
            print(f"[DEBUG] User {username} not found.")
            return None
        
        # Fetch user's tweets
        print(f"[DEBUG] Fetching tweets for user ID: {user.id}")
        tweets = []
        
        # Initial fetch
        batch = await client.get_user_tweets(user.id, tweet_type='Tweets', count=max_tweets)
        if batch:
            tweets.extend(batch)
            print(f"[DEBUG] Retrieved initial batch of {len(batch)} tweets")
            
            # Continue fetching using .next until we reach max_tweets
            while len(tweets) < max_tweets:
                # Add random delay between 0-5 seconds to avoid rate limits
                delay = random.uniform(0, 5)
                print(f"[DEBUG] Adding random delay of {delay:.2f} seconds before fetching next batch")
                time.sleep(delay)
                
                try:
                    batch = await batch.next()
                except TooManyRequests as e:
                    # rate_limit_reset = datetime.fromtimestamp(e.rate_limit_reset)
                    print(f"[DEBUG] Rate limit exceeded. Resetting at {datetime.now()}")
                    # wait_time = (rate_limit_reset - datetime.now()).total_seconds()
                    time.sleep(100)
                    continue

                if batch:
                    tweets.extend(batch)
                    print(f"[DEBUG] Retrieved additional batch, total tweets now: {len(tweets)}")
                else:
                    print(f"[DEBUG] No more tweets available after {len(tweets)} tweets")
                    break
                
                # Break if we've reached or exceeded max_tweets
                if len(tweets) >= max_tweets or batch.next:
                    print(f"[DEBUG] Reached maximum tweet count: {max_tweets}")
                    tweets = tweets[:max_tweets]  # Trim to max_tweets
                    break
        
        print(f"[DEBUG] Retrieved a total of {len(tweets)} tweets for user {username}")
        
        # Prepare CSV file
        file_path = f'{username}_tweets_and_replies_temp.csv'
        print(f"[DEBUG] Creating CSV file: {file_path}")
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Tweet ID', 'Username', 'Text', 'Created At', 'Type', 'Sentiment', 'Score'])
            
            # Iterate through each tweet
            for tweet in tweets:
                # Write original tweet
                tweet_data = get_tweet_data(tweet)
                writer.writerow([
                    tweet_data['id'],
                    tweet_data['username'],
                    tweet_data['text'],
                    tweet_data['created_at'],
                    'Post',
                    map_sentiment_label(tweet_data['sentiment']),
                    tweet_data['score']
                ])
                print(f"[DEBUG] Added tweet {tweet.id} to CSV")
                
                # Fetch and write replies for this tweet using the get_replies_for_tweet function
                print(f"[DEBUG] Fetching replies for tweet {tweet.id}")
                replies = await get_replies_for_tweet(tweet.id)
                print(f"[DEBUG] Retrieved {len(replies)} direct replies for tweet {tweet.id}")
                
                for reply in replies:
                    writer.writerow([
                        reply['id'],
                        reply['username'],
                        reply['text'],
                        reply['created_at'],
                        'Reply',
                        reply['sentiment'],
                        reply['score']
                    ])
                    print(f"[DEBUG] Added reply {reply['id']} to CSV")
        
        print(f"[DEBUG] CSV file created successfully: {file_path}")
        return file_path
    except Exception as e:
        print(f"[DEBUG] Error in fetch_user_tweets_and_replies: {e}")
        logger.error(f"Error in fetch_user_tweets_and_replies: {e}")
        return None