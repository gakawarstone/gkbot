import handlers
import middlewares
import models
from lib.bot import BotManager
from lib.schedule import Schedule
from services.reminder import Reminder
from services.shiki.dispatcher import UserUpdatesDispatcher
from settings import ADMINS, BOT_TOKEN, DB_URL, DEFAULT_COMMANDS, MODELS
from utils.commands import DefaultCommands
from utils.notify import Notifier
from ui.components.base import BaseComponent

mng = BotManager(BOT_TOKEN)

TASKS_ON_STARTUP = [
    models.setup(DB_URL, MODELS),
    DefaultCommands(mng.bot).set(DEFAULT_COMMANDS),
    Schedule.on_startup(),
    UserUpdatesDispatcher.set_bot(mng.bot).on_startup(),
    Notifier.setup(mng.bot, ADMINS),
    Reminder.setup(mng.bot),
    BaseComponent.setup(mng.bot),
]


def start(mng: BotManager = mng):
    mng.add_tasks_on_startup(TASKS_ON_STARTUP)
    middlewares.setup(mng.dp)
    handlers.setup(mng.dp)
    mng.start()
