import os

from dotenv import load_dotenv

load_dotenv()

ADMIN_IDS = os.getenv("ADMIN_IDS")

# Not optional must be set
BOT_TOKEN = os.getenv("BOT_TOKEN")

NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
DB_URL = os.getenv("DB_URL")
API_SERVER_URL = os.getenv("API_SERVER_URL")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TELEGRAPH_API_KEY = os.getenv("TELEGRAPH_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BROKER_URL = os.getenv("BROKER_URL")

DB_DIALECT = os.getenv("SQLDIALECT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
