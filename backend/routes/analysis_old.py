# backend/routes/analysis.py
from fastapi import APIRouter, HTTPException, Depends
from schemas.analysis_request import AnalysisRequest
from schemas.analysis_response import AnalysisResponse, TweetSentiment, SentimentSummary
from service import twitter_service, sentiment_service
from typing import List, Dict, Any
from db.database import get_supabase_client
from db import crud
from supabase import Client

router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_tweets(request_data: AnalysisRequest, supabase: Client = Depends(get_supabase_client)):
    """Analyzes the sentiment of LATEST tweets based on a user query and stores results in DB."""

    # 1. Extract Tweets and Replies
    tweets = await twitter_service.get_tweets(
        request_data.query, request_data.count
    )
    if not tweets:
        raise HTTPException(status_code=404, detail="No tweets found for the given query.")

    all_texts = []
    all_tweets_data = []

    for tweet in tweets:
        all_texts.append(tweet['text'])
        tweet['type'] = 'Post'  # Mark as post
        all_tweets_data.append(tweet)

        """ DUE To Limitation of less replies on Latest Tweets """
        # replies = await twitter_service.get_replies_for_tweet(tweet['id'])
        # for reply in replies:
        #     all_texts.append(reply['text'])
        #     reply['type'] = 'reply'  # Mark as reply
        #     all_tweets_data.append(reply)

    if not all_texts:
        raise HTTPException(status_code=404, detail="No tweets or replies found.")

    # 2 & 3. Analyze Sentiment, Store in DB, and prepare response
    analysis_response_obj = await sentiment_service.perform_sentiment_analysis_and_store(
        supabase, request_data.query, request_data.count, all_tweets_data
    )

    return analysis_response_obj

@router.get("/reports/{username}", response_model=List[AnalysisResponse])
async def get_sentiment_reports_for_user(username: str, supabase: Client = Depends(get_supabase_client)):
    """
    Retrieves sentiment analysis reports for a specific username.
    Returns a list of AnalysisResponse objects.
    """
    db_analyses = crud.get_analysis_report(supabase, username=username)
    if not db_analyses:
        raise HTTPException(status_code=404, detail=f"No analysis reports found for user: {username}")
    print(f"[DEBUG] Found {len(db_analyses)} reporting { username }")
    analysis_responses: List[AnalysisResponse] = []
    for db_analysis in db_analyses:
        top_positive_db = crud.fetch_tweets_by_analysis_id(supabase, analysis_id= db_analysis["analysis_id"], sentiment='positive', tweet_type= 'post', limit= 5)
        top_negative_db = crud.fetch_tweets_by_analysis_id(supabase, analysis_id= db_analysis["analysis_id"], sentiment='negative', tweet_type='post', limit= 5)

        # Convert Supabase records to Response models
        top_positive_response = [TweetSentiment(**tweet) for tweet in top_positive_db]
        top_negative_response = [TweetSentiment(**tweet) for tweet in top_negative_db]
        print(f"[DEBUG] Found top_positive_response: {len(top_positive_response)}, top_negative_response: {top_negative_response}")

        print(f"[DEBUG] check db_analysis:{ db_analysis }")
        # Working Great ===> Later ==> FIX This get None Type Error Or 0.0 || Need to update things on db to get useful info 
        if db_analysis["positive_sentiment_percentage"] is None:
            analysis_summary = SentimentSummary( positive= 0.0, neutral= 0.0, negative= 0.0 )
        else:
            analysis_summary = SentimentSummary(
                positive=float(db_analysis["positive_sentiment_percentage"]),   # Will not return without doing first try
                neutral=float(db_analysis["neutral_sentiment_percentage"]),
                negative=float(db_analysis["negative_sentiment_percentage"])
            )

        # Get all tweets for this analysis
        all_tweets = crud.fetch_tweets_by_analysis_id(supabase, db_analysis["analysis_id"])
        
        analysis_response_item = AnalysisResponse(
            summary=analysis_summary,
            tweets=[TweetSentiment(**tweet) for tweet in all_tweets],
            top_positive=top_positive_response,
            top_neutral=[],  # You can fetch top neutral similarly if needed
            top_negative=top_negative_response,
            graph_data=[]  # You might need to regenerate graph data or store it
        )
        analysis_responses.append(analysis_response_item)

    return analysis_responses