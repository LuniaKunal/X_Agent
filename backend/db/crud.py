# backend/db/crud.py
from fastapi import Query
from typing import List, Dict, Optional, Any
import logging
from supabase import Client
from datetime import datetime
from collections import defaultdict
from dateutil import parser

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Table names in Supabase
ANALYSES_TABLE = "analyses"
TWEETS_TABLE = "tweets"
GRAPH_DATA_TABLE = "graph_data"

def create_analysis(supabase: Client, username: str, query_parameters: Dict) -> Dict[str, Any]:
    """
    Create a new analysis record in the database.
    
    Args:
        supabase: Supabase client
        username: Twitter username being analyzed
        query_parameters: Parameters used for the Twitter query
        
    Returns:
        The created analysis record
    """
    try:
        # Create a new analysis record
        data = {
            "username": username,
            "query_parameters": query_parameters,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        response = supabase.table(ANALYSES_TABLE).insert(data).execute()
        
        if len(response.data) > 0:
            logger.info(f"Created analysis for user {username}")
            return response.data[0]
        else:
            logger.error("Failed to create analysis record")
            raise Exception("Failed to create analysis record")
    except Exception as e:
        logger.error(f"Error creating analysis: {e}")
        raise

def update_analysis_summary(supabase: Client, analysis_id: int, summary: Dict, tweet_count: int) -> Dict[str, Any]:
    """
    Update an existing analysis with sentiment summary data.
    
    Args:
        supabase: Supabase client
        analysis_id: ID of the analysis to update
        summary: Dictionary containing positive, neutral, and negative sentiment percentages
        tweet_count: Number of tweets analyzed
        
    Returns:
        The updated analysis record
    """
    try:
        data = {
            "positive_sentiment_percentage": summary["positive"],
            "neutral_sentiment_percentage": summary["neutral"],
            "negative_sentiment_percentage": summary["negative"],
            "tweet_count": tweet_count
        }
        
        response = supabase.table(ANALYSES_TABLE).update(data).eq("analysis_id", analysis_id).execute()
        
        if len(response.data) > 0:
            logger.info(f"Updated analysis {analysis_id} with sentiment summary")
            return response.data[0]
        else:
            logger.error(f"Failed to update analysis {analysis_id}")
            raise Exception(f"Failed to update analysis {analysis_id}")
    except Exception as e:
        logger.error(f"Error updating analysis: {e}")
        raise

def create_tweet(supabase: Client, tweet_data: Dict, analysis_id: int) -> Dict[str, Any]:
    """
    Create a new tweet record in the database.
    If the tweet already exists, it will be skipped and the existing record will be returned.
    
    Args:
        supabase: Supabase client
        tweet_data: Tweet data including id, type, username, text, created_at, sentiment, and score
        analysis_id: ID of the analysis this tweet belongs to
        
    Returns:
        The created tweet record or the existing one if already in database
    """
    try:
        # Check if the tweet already exists
        existing_tweet = supabase.table(TWEETS_TABLE).select("*").eq("tweet_id", tweet_data["tweet_id"]).execute()
        
        # If the tweet exists, return the existing record
        if len(existing_tweet.data) > 0:
            logger.info(f"Tweet {tweet_data['tweet_id']} already exists, skipping insertion")
            return existing_tweet.data[0]
        
        # Tweet doesn't exist, proceed with insertion
        data = {
            "tweet_id": tweet_data["tweet_id"],
            "analysis_id": analysis_id,
            "type": tweet_data["type"],
            "username": tweet_data["username"],
            "text": tweet_data["text"],
            "created_at": tweet_data["created_at"].isoformat() if isinstance(tweet_data["created_at"], datetime) else tweet_data["created_at"],
            "sentiment": tweet_data["sentiment"],
            "sentiment_score": tweet_data["score"]
        }
        
        response = supabase.table(TWEETS_TABLE).insert(data).execute()
        
        if len(response.data) > 0:
            return response.data[0]
        else:
            logger.error(f"Failed to create tweet record for tweet {tweet_data['id']}")
            raise Exception(f"Failed to create tweet record for tweet {tweet_data['id']}")
    except Exception as e:
        logger.error(f"Error creating tweet: {e}")
        raise

def create_graph_data(supabase: Client, graph_data: List[Dict]) -> List[Dict[str, Any]]:
    """
    Create graph data records in the database for a given analysis.

    Args:
        supabase: Supabase client
        graph_data: List of graph data points, each containing date, positive, neutral, and negative percentages

    Returns:
        List of created graph data records
    """
    try:
        # Insert all graph data points in a single batch
        response = supabase.table(GRAPH_DATA_TABLE).insert(graph_data).execute()

    except Exception as e:
        logger.error(f"Error creating graph data: {e}")
        raise

def get_analysis_report(supabase: Client, username: str) -> List[Dict[str, Any]]:
    """
    Get all analyses for a specific username, ordered by timestamp (newest first).
    
    Args:
        supabase: Supabase client
        username: Twitter username to get analyses for
        
    Returns:
        List of analysis records
    """
    try:
        response = supabase.table(ANALYSES_TABLE)\
            .select("*")\
            .eq("username", username)\
            .order("analysis_timestamp", desc=True)\
            .execute()
            
        return response.data
    except Exception as e:
        logger.error(f"Error getting analysis report: {e}")
        raise

def get_monthly_sentiment_distribution(supabase: Client, username: str, group_by: str = Query("monthly", enum=["monthly", "weekly"])):
    try:
        # Step 1: Get all analysis_ids for this username
        analyses_response = supabase.table(ANALYSES_TABLE)\
            .select("analysis_id")\
            .eq("username", username)\
            .execute()

        analysis_ids = [a["analysis_id"] for a in analyses_response.data]

        # Step 2: Get tweets for those analysis_ids
        tweets_response = supabase.table("tweets")\
            .select("created_at, sentiment")\
            .in_("analysis_id", analysis_ids)\
            .execute()

        tweets = tweets_response.data


        # Step 3: Grouping key
        def get_group_key(created_at):
            dt = parser.parse(created_at)
            return dt.strftime("%Y-%m") if group_by == "monthly" else dt.strftime("%Y-W%U")

        # Step 4: Aggregate sentiment counts
        grouped = defaultdict(lambda: {"positive": 0, "neutral": 0, "negative": 0, "total": 0})

        for tweet in tweets:
            key = get_group_key(tweet["created_at"])
            sentiment = tweet.get("sentiment")
            if sentiment in grouped[key]:
                grouped[key][sentiment] += 1
                grouped[key]["total"] += 1

        # Step 5: Calculate sentiment ratios
        result = []
        for key, counts in sorted(grouped.items()):
            total = counts["total"]
            result.append({
                "time_period": key,
                "total_tweets": total,
                "positive_ratio": round(counts["positive"] / total, 3),
                "neutral_ratio": round(counts["neutral"] / total, 3),
                "negative_ratio": round(counts["negative"] / total, 3),
            })

        return {"data": result}

    except Exception as e:
        return {"error": str(e)}
    
def get_overall_sentiment_summary_for_username(supabase: Client, username: str) -> Dict[str, float]:
    """
    Calculate overall sentiment summary (percentages) for a given username across all analyses.

    Args:
        supabase: Supabase client
        username: Twitter username

    Returns:
        Dictionary containing overall sentiment percentages (positive, neutral, negative).
    """
    try:
        # Step 1: Get all analysis_ids for this username
        analyses_response = supabase.table(ANALYSES_TABLE)\
            .select("analysis_id")\
            .eq("username", username)\
            .execute()
        analysis_ids = [a["analysis_id"] for a in analyses_response.data]

        # Step 2: Fetch sentiments for all tweets under these analysis_ids
        tweets_response = supabase.table(TWEETS_TABLE)\
            .select("sentiment")\
            .in_("analysis_id", analysis_ids)\
            .execute()
        tweets_sentiment_labels = [tweet["sentiment"] for tweet in tweets_response.data]


        # Step 3: Calculate summary from sentiment labels (reuse calculate_summary logic)
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        for label in tweets_sentiment_labels:
            if label in sentiment_counts:
                sentiment_counts[label] += 1
        total_tweets = len(tweets_sentiment_labels)

        summary = {k: round(v / total_tweets, 2) if total_tweets > 0 else 0.0 for k, v in sentiment_counts.items()}
        return summary

    except Exception as e:
        logger.error(f"Error getting overall sentiment summary for username: {e}")
        return {"positive": 0.0, "neutral": 0.0, "negative": 0.0}

def fetch_tweets_by_analysis_id(supabase, analysis_id, sentiment =None, tweet_type=None, limit=None):

    """
    Fetch tweets from Supabase by analysis_id and optional filters.
    Returns data in the format matching TweetSentiment model.
    
    Parameters:
    - supabase: Supabase client
    - analysis_id: ID of the analysis
    - sentiment: Optional filter for sentiment ("positive", "negative", "neutral")
    - tweet_type: Optional filter for tweet type ("post" or "reply")
    - limit: Optional limit for number of results
    
    Returns:
    - List of tweets formatted according to TweetSentiment model
    """
    query = supabase.table(TWEETS_TABLE).select("tweet_id, type, text, username, created_at, sentiment, sentiment_score")
    
    # Apply filters
    query = query.eq("analysis_id", analysis_id)
    
    if sentiment:
        query = query.eq("sentiment", sentiment)
    
    if tweet_type:
        query = query.eq("type", tweet_type)
    
    # Apply ordering and limit
    if limit:
        query = query.limit(limit)
    
    # Execute query
    response = query.execute()
    return transform_tweets_for_response(response.data)

def transform_tweets_for_response(tweets_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transforms tweet data from Supabase response to the format expected by TweetSentiment model."""
    # Transform data to match TweetSentiment model

    transformed_tweets: List[Dict[str, Any]] = []
    for tweet in tweets_data:
        transformed_tweet = {
            "id": str(tweet["tweet_id"]),  # Convert to string as per model
            "type": tweet["type"],
            "text": tweet["text"],
            "username": tweet["username"],
            "created_at": tweet["created_at"],
            "sentiment": tweet["sentiment"],
            "score": float(tweet["sentiment_score"])  # Ensure it's a float
        }
        transformed_tweets.append(transformed_tweet)
     
    return transformed_tweets

def fetch_all_tweets_for_username(supabase: Client, username: str) -> List[Dict[str, Any]]:
    """
    Fetch all tweets for a given username across all their analyses.

    Args:
        supabase: Supabase client
        username: Twitter username

    Returns:
        List of all tweet records for the username.
    """
    try:
        # Step 1: Get all analysis_ids for this username
        analysis_response = supabase.table(ANALYSES_TABLE)\
            .select("analysis_id").eq("username", username).execute()
        analysis_ids = [item["analysis_id"] for item in analysis_response.data]

        # Step 2: Fetch all tweets for these analysis_ids
        tweets_response = supabase.table(TWEETS_TABLE)\
            .select("*").in_("analysis_id", analysis_ids).execute()
        return transform_tweets_for_response(tweets_response.data)

    except Exception as e:
        logger.error(f"Error fetching all tweets for username: {e}")
        return []

def fetch_top_tweets_for_username(supabase: Client, username: str, sentiment: str,tweet_type: str, limit: int) -> List[Dict[str, Any]]:
    """
    Fetch top tweets of a specific sentiment for a given username across all their analyses.

    Args:
        supabase: Supabase client
        username: Twitter username
        sentiment: Sentiment to filter by ('positive' or 'negative')
        tweet_type: Type of tweet ('post' or 'reply')
        limit: Maximum number of top tweets to return

    Returns:
        List of top tweet records.
    """
    try:
        # Step 1: Get all analysis_ids for this username
        analyses_response = supabase.table(ANALYSES_TABLE)\
            .select("analysis_id")\
            .eq("username", username)\
            .execute()
        analysis_ids = [a["analysis_id"] for a in analyses_response.data]

        print(f"[DEBUG] Analysis_ids: {analysis_ids}")
        # Step 2: Fetch tweets for those analysis_ids with specified sentiment and type, order by score
        tweets_response = supabase.table(TWEETS_TABLE)\
            .select("tweet_id, type, text, username, created_at, sentiment, sentiment_score")\
            .in_("analysis_id", analysis_ids)\
            .eq("sentiment", sentiment)\
            .eq("type", tweet_type)\
            .order("sentiment_score", desc=True)\
            .limit(limit)\
            .execute()

        return transform_tweets_for_response(tweets_response.data)

    except Exception as e:
        logger.error(f"Error fetching top tweets for username: {e}")
        return []

# def fetch_latest_tweets_by_username(supabase: Client, username: str) -> Optional[Dict[str, Any]]:
#     """
#     Fetch the most recent analysis and its tweets for a given username.
    
#     Args:
#         supabase: Supabase client
#         username: Twitter username
        
#     Returns:
#         Dictionary containing analysis data and associated tweets, or None if no data exists
#     """
#     try:
#         # Get the most recent analysis for the username
#         analysis = supabase.table(ANALYSES_TABLE)\
#             .select("*")\
#             .eq("username", username)\
#             .order("analysis_timestamp", desc=True)\
#             .limit(1)\
#             .execute()
            
#         if not analysis.data:
#             return None
            
#         analysis_id = analysis.data[0]["analysis_id"]
        
#         # Fetch tweets for this analysis
#         tweets = supabase.table(TWEETS_TABLE)\
#             .select("*")\
#             .eq("analysis_id", analysis_id)\
#             .limit(1)\
#             .execute()
            
#         if not tweets.data:
#             return None
            
#         print(f"[DEBUG] Returning from Fetch Latest: analysis: {analysis.data[0]}, tweets:{transform_tweets_for_response(tweets.data)}")
#         return {
#             "analysis": analysis.data[0],
#             "tweets": transform_tweets_for_response(tweets.data)
#         }
        
#     except Exception as e:
#         logger.error(f"Error fetching tweets by username: {e}")
#         return None

def fetch_latest_tweets_by_username(supabase: Client, username: str) -> Optional[Dict[str, Any]]:
    """
    Fetch the most recent analysis and its tweets for a given username.
    
    Args:
        supabase: Supabase client
        username: Twitter username
        
    Returns:
        Dictionary containing analysis data and associated tweets, or None if no data exists
    """
    try:
        # Get today's date in the format YYYY-MM-DD
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get the most recent analysis for the username with current timestamp
        analysis = supabase.table(ANALYSES_TABLE)\
            .select("*")\
            .eq("username", username)\
            .eq("analysis_timestamp", today)\
            .limit(1)\
            .execute()
            
        # If no analysis for today, fall back to the most recent one
        if not analysis.data:
            return False # I don't have latest data
    except Exception as e:
        logger.error(f"Error checking tweet existence: {e}")
        return False
    

def check_tweet_exists(supabase: Client, tweet_id: str) -> bool:
    """
    Check if a tweet already exists in the database.
    
    Args:
        supabase: Supabase client
        tweet_id: ID of the tweet to check
        
    Returns:
        bool: True if tweet exists, False otherwise
    """
    try:
        result = supabase.table(TWEETS_TABLE)\
            .select("tweet_id")\
            .eq("tweet_id", tweet_id)\
            .execute()
        
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Error checking tweet existence: {e}")
        return False