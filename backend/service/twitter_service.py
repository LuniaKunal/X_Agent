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
from service.sentiment_service import analyze_sentiment
from utils.helpers import map_sentiment_label
from db import crud
from db.database import get_supabase_client
from service.sentiment_service import calculate_summary, prepare_graph_data
from schemas.user_tweets_response import UserTweetsResponse, TweetData


# Set up basic logging
print("Loading twitter_service.py module")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def load_cookies(filename: str) -> Optional[dict]:
    try:
        with open(filename, 'r') as f:
            cookies = json.load(f)
        return cookies
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[DEBUG] Error loading cookies: {e}")
        logger.error(f"Error loading cookies from {filename}: {e}")
        return None

async def get_tweets(query: str, count: int) -> List[dict]:
    client = Client('en-US')

    cookies = await load_cookies(settings.TWIKIT_COOKIES_FILE)
    if not cookies:
        print("[DEBUG] No cookies loaded, returning empty tweet list")
        return []
    client.set_cookies(cookies)
    try:
        tweets = await client.search_tweet(query, 'Latest', count=count)

        tweet_data = [get_tweet_data(tweet) for tweet in tweets]
        return tweet_data
    except Exception as e:
        logger.error(f"Error during tweet retrieval: {e}")
        return []

async def get_replies_for_tweet(tweet_id: int) -> List[Dict]:
    """
    Fetches direct replies for a given tweet ID using pagination.
    Adds a random delay between 0-5 seconds to avoid rate limits.
    """

    try:
        # Fetch replies using pagination
        replies = await get_replies(str(tweet_id), count=30)

        if replies:
            reply_texts = [reply.text for reply in replies]
            sentiments = analyze_sentiment(reply_texts)

            for reply, sentiment in zip(replies, sentiments):
                reply.sentiment = map_sentiment_label(sentiment['label'])
                reply.score = sentiment['score']

            return [get_tweet_data(reply) for reply in replies]
        return []
    except Exception as e:
        logger.error(f"Error fetching replies for tweet {tweet_id}: {e}")
        return []

async def get_replies(tweet_id: str, count: int) -> list:
    """
    Fetch up to `count` replies for a given tweet_id using pagination.
    """
    client = Client('en-US')
    all_replies = []
    cursor = ""

    try:
        # Load cookies
        cookies = await load_cookies(settings.TWIKIT_COOKIES_FILE)
        if not cookies:
            return []

        client.set_cookies(cookies)

        while len(all_replies) < count:
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

            if not hasattr(result, 'next_cursor'):
                break

            cursor = result.next_cursor

        return all_replies

    except Exception as e:
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
        logger.error(f"Error processing tweet data: {e}")
        return {'error': str(e)}

async def fetch_user_tweets_and_replies(username: str, max_tweets: int, supabase: Client):
    """
    Fetch tweets and replies for a specific user.
    First checks database for existing tweets, if not found fetches from Twitter.
    Uses the .next function to retrieve more tweets and adds random delays to avoid rate limits.
    Stores tweets and replies in Supabase database.

    Args:
        username: Twitter username to fetch tweets for.
        max_tweets: Maximum number of tweets to fetch.
        supabase: Supabase client for database interaction.

    Returns:
        UserTweetsResponse: Structured response containing fetched tweets data.
    """
    # First try to get tweets from database
    existing_data = crud.fetch_latest_tweets_by_username(supabase, username)
    if existing_data:
        logger.info(f"Found existing tweets in database for user {username}")
        logger.info(f"We Already have the latest tweets for the user {username}")
        return UserTweetsResponse(
            username= username,
            tweet_count = 0, # No Need to do any operations as we already have latest data
            tweets=[],
        )

    # If no tweets in database, fetch from Twitter
    client = Client('en-US')
    tweets_data_list: List[Dict] = []

    cookies = await load_cookies(settings.TWIKIT_COOKIES_FILE)
    if not cookies:
        return None
    client.set_cookies(cookies)

    try:
        user = await client.get_user_by_screen_name(username)
        if not user:
            return [f"User {username} not found."]

        tweets_batch = await client.get_user_tweets(user.id, tweet_type='Tweets', count=max_tweets)
        if not tweets_batch:
            return [(f"[DEBUG] No tweets found for user: {username}")]

        tweets = []
        tweets.extend(tweets_batch)  # --> Thought is this is getting more tweets than asked

        analysis = crud.create_analysis(supabase, username=username, query_parameters={"max_tweets": max_tweets})
        analysis_id = analysis["analysis_id"]
        logger.info(f"Created analysis record with ID: {analysis_id}")

        for tweet in tweets:
            tweet_data = get_tweet_data(tweet)
            tweet_data['type'] = 'Post'
            
            # Skip if tweet already exists in database
            if crud.check_tweet_exists(supabase, str(tweet_data['id'])):
                logger.info(f"Tweet {tweet_data['id']} already exists in database, skipping")
                break
                
            tweet_db_data = await store_tweet_and_replies_with_sentiment(supabase, tweet_data, analysis_id)
            tweets_data_list.append(tweet_db_data)
            
            replies = await get_replies_for_tweet(tweet_data['id'])
            print(f"[DEBUG] These are the replies fetched :: {len(replies)}")
            for reply in replies:
                reply_data = reply
                reply_data['type'] = 'Reply'
                print(f"[DEBUG] Checking replys in DB or Storing in the database")
                # Skip if reply already exists in database
                reply_db_data = await store_tweet_and_replies_with_sentiment(supabase, reply_data, analysis_id)
                tweets_data_list.append(reply_db_data)

        if not tweets_data_list:
            return UserTweetsResponse(
            username= username,
            tweet_count = 0, # No Need to do any operations
            tweets=[],
        )

        # Calculate sentiment summary and graph data
        all_sentiments = [tweet['sentiment'] for tweet in tweets_data_list if 'sentiment' in tweet]
        sentiment_summary = calculate_summary(all_sentiments)

        # Update analysis with summary
        crud.update_analysis_summary(supabase, analysis_id, sentiment_summary, len(tweets_data_list))

        graph_data = prepare_graph_data(sentiment_summary, analysis_id, username)

        # Store graph data
        crud.create_graph_data(supabase, graph_data)

        return UserTweetsResponse(
            username= username,
            tweet_count=len(tweets_data_list),
            tweets=[TweetData(**tweet) for tweet in tweets_data_list],
        )

    except Exception as e:
        logger.error(f"Error during tweet retrieval: {e}")
        return None

async def store_tweet_and_replies_with_sentiment(supabase: Client, tweet_data: Dict, analysis_id: int) -> Dict:
    """
    Analyzes sentiment of a tweet and its replies, stores tweet and replies in Supabase.
    """
    text = tweet_data['text']
    sentiment_results = analyze_sentiment([text])
    sentiment = sentiment_results[0] if sentiment_results else {}

    # Prepare tweet data for database
    db_tweet_data = {
        "tweet_id": tweet_data['id'],
        "type": tweet_data['type'],
        "username": tweet_data['username'],
        "text": text,
        "created_at": tweet_data['created_at'],
        "sentiment": map_sentiment_label(sentiment.get('label', 'neutral')),
        "score": float(sentiment.get('score', 0.0))
    }
    stored_tweet = crud.create_tweet(supabase, db_tweet_data, analysis_id)
    return db_tweet_data