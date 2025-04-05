# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from routes import analysis, user_tweets
from db.database import get_supabase_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Twitter Sentiment Analysis API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(user_tweets.router, prefix="/api", tags=["user-tweets"])

@app.on_event("startup")
async def startup():
    """
    Initialize Supabase client and verify connection on startup
    """
    try:
        # Test Supabase connection
        supabase = get_supabase_client()
        # Try a simple query to verify connection
        supabase.table("analyses").select("*").limit(1).execute()
        logger.info("Successfully connected to Supabase")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        raise

@app.get("/")
async def root():
    """
    Root endpoint for API health check
    """
    return {"status": "ok", "message": "Twitter Sentiment Analysis API is running"}