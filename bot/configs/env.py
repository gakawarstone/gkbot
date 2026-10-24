import os

from dotenv import load_dotenv

from core.types import DEFAULT_POLLING_TASKS_CONCURRENCY_LIMIT

load_dotenv()


def _get_required_env(key: str) -> str:
    value = os.getenv(key)
    if value is None or value == "":
        raise ValueError(f"{key} is required")
    return value


def _get_positive_int_env(key: str, default: int) -> int:
    try:
        value = int(os.getenv(key, str(default)))
    except ValueError as error:
        raise ValueError(f"{key} must be a positive integer") from error
    if value <= 0:
        raise ValueError(f"{key} must be a positive integer")
    return value


BOT_TOKEN = _get_required_env("BOT_TOKEN")
ADMIN_IDS = _get_required_env("ADMIN_IDS")
POLLING_TASKS_CONCURRENCY_LIMIT = _get_positive_int_env(
    "POLLING_TASKS_CONCURRENCY_LIMIT", DEFAULT_POLLING_TASKS_CONCURRENCY_LIMIT
)

NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
DB_URL = os.getenv("DB_URL")
API_SERVER_URL = os.getenv("API_SERVER_URL")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TELEGRAPH_API_KEY = os.getenv("TELEGRAPH_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BROKER_URL = os.getenv("BROKER_URL")

DB_DIALECT: str | None
DB_USER: str | None
DB_PASSWORD: str | None
DB_HOST: str | None
DB_PORT: str | None
DB_NAME: str | None

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
