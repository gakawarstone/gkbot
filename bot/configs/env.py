import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
DB_URL = os.getenv("DB_URL")
API_SERVER_URL = os.getenv("API_SERVER_URL")
