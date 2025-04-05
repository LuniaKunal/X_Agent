# backend/app/schemas/user_tweets_response.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TweetData(BaseModel):
    tweet_id: str
    username: str
    text: str
    created_at: str
    type: str  # 'Post' or 'Reply'

class UserTweetsResponse(BaseModel):
    username: str
    tweet_count: int
    tweets: List[TweetData]
    file_path: Optional[str] = None
