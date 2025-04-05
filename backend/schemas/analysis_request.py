# backend/app/schemas/analysis_request.py
from pydantic import BaseModel, Field, validator

class AnalysisRequest(BaseModel):
    query: str = Field(..., description="Twitter username or search query")
    count: int = Field(
        ...,
        description="Number of tweets to analyze",
    )

    @validator("count")
    def count_must_be_positive_and_within_limits(cls, value):
        from core.config import settings
        if value <= 0:
            raise ValueError("Count must be a positive integer")
        if value > settings.MAX_TWEET_COUNT:
            raise ValueError(f"Count cannot exceed {settings.MAX_TWEET_COUNT}")
        return value