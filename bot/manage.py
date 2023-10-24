import handlers
import middlewares
import models
from core.bot import BotManager
from core.default_commands import DefaultCommands
from core.notifier import Notifier
from services.schedule import Schedule
from settings import API_SERVER_URL, BOT_TOKEN, DB_URL, DEFAULT_COMMANDS, MODELS

mng = BotManager(BOT_TOKEN, API_SERVER_URL)

TASKS_ON_STARTUP = [
    models.setup(DB_URL, MODELS),
    DefaultCommands(DEFAULT_COMMANDS).set(mng.bot),
    Schedule.on_startup(),
    Notifier.setup(mng.bot),
]


def start(mng: BotManager = mng):
    mng.add_tasks_on_startup(TASKS_ON_STARTUP)
    middlewares.setup(mng.dp)
    handlers.setup(mng.dp)
    mng.start()
