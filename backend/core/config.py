import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    TWIKIT_COOKIES_FILE: str = os.getenv("TWIKIT_COOKIES_FILE", "cookies.json")
    DEFAULT_TWEET_COUNT: int = int(os.getenv("DEFAULT_TWEET_COUNT", "50"))
    MAX_TWEET_COUNT: int = int(os.getenv("MAX_TWEET_COUNT", "200"))
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")  # Supabase URL from your project settings
    SUPABASE_API_KEY: str = os.getenv("SUPABASE_API_KEY") # Supabase API Key (anon or service_role)
    DATABASE_URL: str = os.getenv("DATABASE_URL") # Directly use DATABASE_URL from Supabase if provided

settings = Settings()

# Print diagnostic information about environment variables
if not settings.SUPABASE_URL:
    print("Error: SUPABASE_URL is not set in environment variables.")
if not settings.SUPABASE_API_KEY:
    print("Error: SUPABASE_API_KEY is not set in environment variables.")
if not settings.DATABASE_URL:
    print("Error: DATABASE_URL is not set in environment variables. Please configure your Supabase connection.")
else:
    # Don't print the full URL with credentials for security reasons
    print(f"Database URL is configured. Using host: {settings.DATABASE_URL.split('@')[1].split('/')[0] if '@' in settings.DATABASE_URL else 'unknown'}")