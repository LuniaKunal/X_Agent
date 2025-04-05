sentiment-analysis-app/
├── backend/
│   ├── app/
│   │   ├── main.py                 # Main FastAPI application
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── analysis.py       # Routes for sentiment analysis
|   |   |-- user_tweets.py    # Routes for fetching Tweets and replies
│   ├── services/
│   │   ├── __init__.py
│   │   ├── twitter_service.py  # Logic for interacting with Twikit
│   │   ├── sentiment_service.py # Logic for sentiment analysis
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user_tweets_response.py # Pydantic models for response data
│   │   ├── analysis_request.py # Pydantic models for request validation
│   │   ├── analysis_response.py# Pydantic models for response data
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── helpers.py         # Utility functions (e.g., data formatting)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration settings (API keys, etc.) -  .env file
│   ├── requirements.txt          # Project dependencies
│   ├── .env.example                # Example environment variables



How to Start the project ::

1. cd backend
2. Create virtual environment, activate it
3. pip install -r requirements.txt
4. python -m uvicorn app.main:app --reload


Libraries Used --> 
fastapi
uvicorn
pydantic[email]
python-dotenv
twikit
transformers
torch
aiofiles
supabase

Database --> Supabase:
Pass --> X_Agent@!123