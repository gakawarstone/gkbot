from core.types import BotConfig

from . import env
from .admins import ADMINS
from .default_commands import DEFAULT_COMMANDS
from .startup import STARTUP_HOOKS

if env.BOT_TOKEN is None:
    raise ValueError("BOT_TOKEN must be set")

BOT_CONFIG = BotConfig(
    token=env.BOT_TOKEN,
    startup_hooks=STARTUP_HOOKS,
    api_url=env.API_SERVER_URL or "https://api.telegram.org",
    default_commands=DEFAULT_COMMANDS,
    parse_mode="HTML",
    admins=ADMINS,
)
