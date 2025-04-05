# backend/schemas/analysis_response.py
from typing import List, Dict
from pydantic import BaseModel

class TweetSentiment(BaseModel):
    id: str
    type: str  # "post" or "reply"
    text: str
    username: str
    created_at: str
    sentiment: str  # "positive", "neutral", "negative"
    score: float

class SentimentSummary(BaseModel):
    positive: float
    neutral: float
    negative: float

class AnalysisResponse(BaseModel):
    tweets: List[TweetSentiment]
    summary: SentimentSummary
    top_positive: List[TweetSentiment]
    top_neutral: List[TweetSentiment]
    top_negative: List[TweetSentiment]
    graph_data: List[Dict]
