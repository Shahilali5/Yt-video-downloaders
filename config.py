from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
