import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _get_required_env(key: str) -> str:
    value = os.getenv(key)
    if value is None or value == "":
        raise ValueError(f"{key} is required")
    return value


BOT_TOKEN = _get_required_env("BOT_TOKEN")
ADMIN_IDS = _get_required_env("ADMIN_IDS")

NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
DB_URL = os.getenv("DB_URL")
API_SERVER_URL = os.getenv("API_SERVER_URL")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TELEGRAPH_API_KEY = os.getenv("TELEGRAPH_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BROKER_URL = os.getenv("BROKER_URL")

DB_DIALECT: Optional[str]
DB_USER: Optional[str]
DB_PASSWORD: Optional[str]
DB_HOST: Optional[str]
DB_PORT: Optional[str]
DB_NAME: Optional[str]

if DB_URL:
    DB_DIALECT = os.getenv("SQLDIALECT")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
else:
    DB_DIALECT = _get_required_env("SQLDIALECT")
    DB_USER = _get_required_env("DB_USER")
    DB_PASSWORD = _get_required_env("DB_PASSWORD")
    DB_HOST = _get_required_env("DB_HOST")
    DB_PORT = _get_required_env("DB_PORT")
    DB_NAME = _get_required_env("DB_NAME")
