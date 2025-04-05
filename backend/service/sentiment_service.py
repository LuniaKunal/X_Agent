# backend/service/sentiment_service.py
from transformers import pipeline
from typing import List, Dict, Tuple
from functools import lru_cache
import logging
import time
from datetime import datetime
from supabase import Client
from utils.helpers import map_sentiment_label
import sys
import os
from schemas import analysis_response
from db import crud

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_sentiment_pipeline():
    """
    Loads the sentiment analysis model, cached for efficiency.
    """
    logger.info("Loading sentiment analysis model")
    start_time = time.time()
    sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")
    end_time = time.time()
    logger.info(f"Sentiment model loaded in {end_time - start_time:.2f} seconds")
    return sentiment_pipeline

def analyze_sentiment(texts: List[str]) -> List[Dict]:
    """
    Analyzes the sentiment of a list of texts.
    """
    if not texts:
        logger.warning("No texts provided for sentiment analysis")
        return []

    sentiment_pipeline = get_sentiment_pipeline()
    
    try:
        results = sentiment_pipeline(texts)
        return results
    except Exception as e:
        logger.error(f"Error during sentiment analysis: {e}")
        return []

def calculate_summary(sentiments: List[str]) -> Dict[str, float]:
    """
    Calculates the percentage of positive, neutral, and negative sentiments.
    """
    logger.info(f"Calculating summary for {len(sentiments)} sentiments")
    print(f"Sentiments list: {sentiments}")
    total = len(sentiments)
    if total == 0:
        return {"positive": 0.0, "neutral": 0.0, "negative": 0.0}

    positive_count = sentiments.count("positive")
    neutral_count = sentiments.count("neutral")
    negative_count = sentiments.count("negative")

    summary = {
        "positive": round(positive_count / total, 2),
        "neutral": round(neutral_count / total, 2),
        "negative": round(negative_count / total, 2),
    }
    logger.info(f"Sentiment summary: {summary}")
    return summary

def get_top_tweets(tweets: List[Dict], key: str, n: int = 5) -> List[Dict]:
    """Gets the top N tweets for a given sentiment."""
    logger.info(f"Getting top {n} tweets for sentiment '{key}'")
    filtered_tweets = [tweet for tweet in tweets if map_sentiment_label(tweet["sentiment"]) == key]
    sorted_tweets = sorted(filtered_tweets, key=lambda x: x["score"], reverse=True)[:n]
    return sorted_tweets

def prepare_graph_data(summary: Dict, analysis_id: int ,query: str):
    graph_data = [{
        "analysis_id": analysis_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "positive": summary["positive"],
        "neutral": summary["neutral"],
        "negative": summary["negative"],
        "username": query,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
    }]
    return graph_data

async def perform_sentiment_analysis_and_store(supabase: Client, query: str, count: int, tweets_data: List[Dict]) -> analysis_response.AnalysisResponse:
    """
    Performs sentiment analysis, stores results in Supabase, and returns analysis response.
    Skips tweets that already exist in the database.
    """
    logger.info(f"Starting sentiment analysis for query '{query}' with {len(tweets_data)} tweets")

    # 1. Create Analysis record in Supabase
    db_analysis = crud.create_analysis(supabase, username=query, query_parameters={"count": count})
    analysis_id = db_analysis["analysis_id"]
    logger.info(f"Created analysis record with ID: {analysis_id}")

    all_texts = []
    all_processed_tweets = []

    for tweet_item in tweets_data:
        all_texts.append(tweet_item['text'])
        tweet_item['type'] = tweet_item.get('type', 'Post')  # Use existing type or default to 'Post'
        all_processed_tweets.append(tweet_item)

    # 2. Analyze Sentiment
    logger.info("Analyzing sentiment for all texts")
    sentiments = analyze_sentiment(all_texts)

    processed_tweets_for_response = []
    all_sentiments = []

    # 3. Process Results and Store Tweets in Supabase
    logger.info("Processing sentiment results and storing tweets")
    for i, sentiment_result in enumerate(sentiments):
        sentiment_label = sentiment_result['label']
        score = sentiment_result['score']
        tweet_data = all_processed_tweets[i]

        # Store sentiment for summary calculation
        all_sentiments.append(map_sentiment_label(sentiment_label))

        # Prepare tweet data for Supabase
        db_tweet_data = {
            "id": tweet_data['id'],
            "type": tweet_data['type'],
            "username": tweet_data['username'],
            "text": tweet_data['text'],
            "created_at": tweet_data['created_at'].isoformat() if isinstance(tweet_data['created_at'], datetime) else tweet_data['created_at'],
            "sentiment": map_sentiment_label(sentiment_label),
            "score": float(score)  # Changed from "sentiment_score" to "score"
        }

        processed_tweets_for_response.append(db_tweet_data) # it should match schema of TweetSentiment Need to input ID
        # Changing format for crud operations
        modified_tweet_data = db_tweet_data.copy()
        modified_tweet_data["tweet_id"] = modified_tweet_data.pop("id")
        # Store tweet in Supabase, skipping if it already exists
        stored_tweet = crud.create_tweet(supabase, modified_tweet_data, analysis_id) # Need to input twitter_id

    # 4. Calculate sentiment summary
    logger.info("Calculating sentiment summary")
    sentiment_summary = calculate_summary(all_sentiments)  # all_sentiments consist of labels like LABEL_1, LABEL_2 etc.

    # 5. Update analysis with summary
    logger.info("Updating analysis with summary")
    updated_analysis = crud.update_analysis_summary(
        supabase,
        analysis_id,
        sentiment_summary,
        len(processed_tweets_for_response)
    )

    # 6. Get top tweets for each sentiment
    logger.info("Getting top tweets for each sentiment")
    top_positive = get_top_tweets(processed_tweets_for_response, "positive")
    top_neutral = get_top_tweets(processed_tweets_for_response, "neutral")
    top_negative = get_top_tweets(processed_tweets_for_response, "negative")

    # 7. Prepare graph data
    logger.info("Preparing graph data")
    graph_data = prepare_graph_data(summary = sentiment_summary, analysis_id = analysis_id, query = query)

    # 8. Store graph data in Supabase ==> Need to be Fixed the Issue to that date format is not correct.
    logger.info("Storing graph data in Supabase")
    stored_graph_data = crud.create_graph_data(supabase, graph_data)

    # 9. Create and return response
    logger.info("Creating analysis response")
    try:
        response = analysis_response.AnalysisResponse(
            summary=analysis_response.SentimentSummary(**sentiment_summary),
            tweets=[analysis_response.TweetSentiment(**tweet) for tweet in processed_tweets_for_response],
            top_positive=[analysis_response.TweetSentiment(**tweet) for tweet in top_positive],
            top_neutral=[analysis_response.TweetSentiment(**tweet) for tweet in top_neutral],
            top_negative=[analysis_response.TweetSentiment(**tweet) for tweet in top_negative],
            graph_data=graph_data
        )
    except Exception as e:
        logger.error(f"Error creating analysis response: {e}")
        raise

    logger.info("Sentiment analysis and storage completed successfully")
    return response