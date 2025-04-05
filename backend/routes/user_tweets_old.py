# backend/routes/user_tweets.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from schemas.user_tweets_request import UserTweetsRequest
from schemas.user_tweets_response import UserTweetsResponse, TweetData
from service import twitter_service
from service.sentiment_service import analyze_sentiment
from utils.helpers import map_sentiment_label
from db import crud
import os
import logging
from typing import List
from db.database import get_supabase_client


# Set up basic logging
print("Loading user_tweets.py router module")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/user-tweets", response_model=UserTweetsResponse)
async def get_user_tweets(request_data: UserTweetsRequest, supabase=Depends(get_supabase_client)):
    """
    Fetches tweets and replies for a specific Twitter user.
    Returns structured data, generates a CSV file, and stores data in Supabase.
    """
    print(f"[DEBUG] Starting get_user_tweets with username: {request_data.username}, max_tweets: {request_data.max_tweets}")
    logger.info(f"Fetching tweets for user: {request_data.username}, max_tweets: {request_data.max_tweets}")
    
    # Fetch tweets and generate CSV
    file_path = await twitter_service.fetch_user_tweets_and_replies(
        request_data.username, 
        request_data.max_tweets,
        supabase
    )
    
    if not file_path:
        print(f"[DEBUG] Failed to fetch tweets for user {request_data.username}")
        raise HTTPException(status_code=404, detail=f"Could not fetch tweets for user: {request_data.username}")
    
    # Read the CSV to create response data
    tweets_data = []
    raw_tweets = []
    try:
        import csv
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            for row in reader:
                if len(row) >= 5:  # Ensure we have all expected columns
                    tweet_data = TweetData(
                        tweet_id=row[0],
                        username=row[1],
                        text=row[2],
                        created_at=row[3],
                        type=row[4]
                    )
                    tweets_data.append(tweet_data)
                    
                    # Add raw tweet data for sentiment analysis and database storage
                    raw_tweets.append({
                        'id': row[0],
                        'username': row[1],
                        'text': row[2],
                        'created_at': row[3],
                        'type': row[4]
                    })
    except Exception as e:
        print(f"[DEBUG] Error reading CSV file: {e}")
        logger.error(f"Error reading CSV file: {e}")
        raise HTTPException(status_code=500, detail="Error processing tweet data")
    
    # Store tweets in Supabase
    try:
        # Create analysis record
        analysis = crud.create_analysis(
            supabase, 
            username=request_data.username, 
            query_parameters={"max_tweets": request_data.max_tweets}
        )
        analysis_id = analysis["analysis_id"]
        logger.info(f"Created analysis record with ID: {analysis_id}")
        
        # Analyze sentiment for all tweets
        all_texts = [tweet['text'] for tweet in raw_tweets]
        sentiment_results = analyze_sentiment(all_texts)
        
        # Process and store each tweet
        for i, tweet in enumerate(raw_tweets):
            if i < len(sentiment_results):
                sentiment = sentiment_results[i]
                sentiment_label = map_sentiment_label(sentiment['label'])
                score = sentiment['score']
                
                # Prepare tweet data for Supabase
                db_tweet_data = {
                    "id": tweet['id'],
                    "type": tweet['type'],
                    "username": tweet['username'],
                    "text": tweet['text'],
                    "created_at": tweet['created_at'],
                    "sentiment": sentiment_label,
                    "score": float(score)
                }
                
                # Store tweet in Supabase
                crud.create_tweet(supabase, db_tweet_data, analysis_id)
        
        # Calculate sentiment summary
        sentiments = [map_sentiment_label(result['label']) for result in sentiment_results]
        positive_count = sentiments.count("positive")
        neutral_count = sentiments.count("neutral")
        negative_count = sentiments.count("negative")
        total = len(sentiments)
        
        if total > 0:
            summary = {
                "positive": round(positive_count / total, 2),
                "neutral": round(neutral_count / total, 2),
                "negative": round(negative_count / total, 2)
            }
            
            # Update analysis with summary
            crud.update_analysis_summary(supabase, analysis_id, summary, len(raw_tweets))
            
            # Prepare and store graph data
            graph_data = [{
                "analysis_id": analysis_id,
                "date": tweet['created_at'].split(' ')[0] if ' ' in tweet['created_at'] else tweet['created_at'],
                "positive": summary["positive"],
                "neutral": summary["neutral"],
                "negative": summary["negative"],
                "username": request_data.username,
                "created_at": tweet['created_at']
            }]
            
            crud.create_graph_data(supabase, graph_data)
            
        logger.info(f"Successfully stored {len(raw_tweets)} tweets in database")
    except Exception as e:
        logger.error(f"Error storing tweets in database: {e}")
        print(f"[DEBUG] Error storing tweets in database: {e}")
        # Continue with response even if database storage fails
    
    # Create response
    response = UserTweetsResponse(
        username=request_data.username,
        tweet_count=len(tweets_data),
        tweets=tweets_data,
        file_path=file_path
    )
    
    print(f"[DEBUG] Successfully processed {len(tweets_data)} tweets for user {request_data.username}")
    return response

# @router.get("/user-tweets/download/{username}")
# async def download_user_tweets_csv(username: str):
#     """
#     Downloads the CSV file of tweets and replies for a specific user.
#     """
#     print(f"[DEBUG] Request to download CSV for user: {username}")
#     file_path = f"{username}_tweets_and_replies.csv"
    
#     if not os.path.exists(file_path):
#         print(f"[DEBUG] CSV file not found for user: {username}")
#         raise HTTPException(status_code=404, detail=f"No CSV file found for user: {username}")
    
#     print(f"[DEBUG] Returning CSV file: {file_path}")
#     return FileResponse(
#         path=file_path, 
#         filename=f"{username}_tweets_and_replies.csv",
#         media_type="text/csv"
#     )

#  --> This will be later changed to get summery and day wise graph data to create chart
@router.get("/user-tweets/download/{username}") # Define download route
async def download_user_tweets_csv(username: str): # Define download route function
   raise HTTPException(status_code=400, detail="CSV download is no longer supported.")