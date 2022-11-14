import handlers
import middlewares
import models
from lib.bot import BotManager
from lib.notifier import Notifier
from lib.schedule import Schedule
from settings import (API_SERVER_URL, BOT_TOKEN, DB_URL,
                      DEFAULT_COMMANDS, MODELS)
from utils.commands import DefaultCommands

mng = BotManager(BOT_TOKEN, API_SERVER_URL)

TASKS_ON_STARTUP = [
    models.setup(DB_URL, MODELS),
    DefaultCommands(mng.bot).set(DEFAULT_COMMANDS),
    Schedule.on_startup(),
    Notifier.setup(mng.bot),
]


def start(mng: BotManager = mng):
    mng.add_tasks_on_startup(TASKS_ON_STARTUP)
    middlewares.setup(mng.dp)
    handlers.setup(mng.dp)
    mng.start()
