# backend/app/schemas/user_tweets_request.py
from pydantic import BaseModel, Field, validator

class UserTweetsRequest(BaseModel):
    username: str = Field(..., description="Twitter username to fetch tweets from")
    max_tweets: int = Field(
        50,
        description="Maximum number of tweets to fetch",
    )

    @validator("max_tweets")
    def max_tweets_must_be_positive_and_within_limits(cls, value):
        from core.config import settings
        if value <= 0:
            raise ValueError("Max tweets must be a positive integer")
        if value > settings.MAX_TWEET_COUNT:
            raise ValueError(f"Max tweets cannot exceed {settings.MAX_TWEET_COUNT}")
        return value
