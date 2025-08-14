from core.types import BotConfig
from . import env
from .startup import TASKS_ON_STARTUP_ASYNC, TASKS_ON_STARTUP_SYNC
from .default_commands import DEFAULT_COMMANDS
from .admins import ADMINS


if env.BOT_TOKEN is None:
    raise ValueError("BOT_TOKEN must be set")

BOT_CONFIG = BotConfig(
    token=env.BOT_TOKEN,
    tasks_on_startup_async=TASKS_ON_STARTUP_ASYNC,
    tasks_on_startup_sync=TASKS_ON_STARTUP_SYNC,
    api_url=env.API_SERVER_URL or "https://api.telegram.org",
    default_commands=DEFAULT_COMMANDS,
    parse_mode="HTML",
    admins=ADMINS,
)
