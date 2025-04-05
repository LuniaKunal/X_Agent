# backend/db/database.py
import os
from supabase import create_client, Client
from core.config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Supabase credentials from environment variables or settings
SUPABASE_URL = settings.SUPABASE_URL or os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = settings.SUPABASE_API_KEY or os.getenv("SUPABASE_API_KEY")

# Check if credentials are available
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is not set. Please check your .env file or environment variables.")
if not SUPABASE_API_KEY:
    raise ValueError("SUPABASE_API_KEY is not set. Please check your .env file or environment variables.")

# Create Supabase client
try:
    logger.info(f"Connecting to Supabase at {SUPABASE_URL}")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)
    logger.info("Successfully connected to Supabase")
except Exception as e:
    logger.error(f"Failed to connect to Supabase: {e}")
    raise

def get_supabase_client():
    """
    Returns the Supabase client for database operations.
    Used as a dependency in FastAPI routes.
    """
    return supabase