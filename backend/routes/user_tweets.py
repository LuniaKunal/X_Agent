from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import FileResponse
from schemas.user_tweets_request import UserTweetsRequest
from schemas.user_tweets_response import UserTweetsResponse, TweetData
from service import twitter_service
import os
import logging
from typing import List
from db.database import get_supabase_client
from supabase import Client
from db.crud import get_monthly_sentiment_distribution


# Set up basic logging
print("Loading user_tweets.py router module")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/user-tweets", response_model=UserTweetsResponse)
async def get_user_tweets(request_data: UserTweetsRequest, supabase: Client =Depends(get_supabase_client)):
    """
    Fetches tweets and replies for a specific Twitter user.
    Returns structured data, generates a CSV file, and stores data in Supabase.
    """

    logger.info(f"Fetching tweets for user: {request_data.username}, max_tweets: {request_data.max_tweets}")

    response = await twitter_service.fetch_user_tweets_and_replies(
        request_data.username,
        request_data.max_tweets,
        supabase
    )

    if not response:

        raise HTTPException(status_code=404, detail=f"Could not fetch tweets for user: {request_data.username}")
    return response

@router.get("/user-tweets/weekly_or_monthly_analysis/{username}")
async def weekly_or_monthly_analysis(username: str, group_by: str = Query("monthly", enum=["monthly", "weekly"]), supabase: Client = Depends(get_supabase_client)):
    """
    Returns weekly or monthly analysis for a specific user.
    """
    try:
        return get_monthly_sentiment_distribution(supabase, username, group_by)
    except Exception as e:
        logger.error(f"Error getting weekly or monthly analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get weekly or monthly analysis: {e}")