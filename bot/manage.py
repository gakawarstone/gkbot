from settings import ADMINS, TASKS_ON_STARTUP, mng
from lib.bot import BotManager
import middlewares
import handlers
from utils.notify import notify_admins


def start(mng: BotManager = mng):
    mng.admins = ADMINS
    mng.add_tasks_on_startup(TASKS_ON_STARTUP)
    middlewares.setup(mng)
    handlers.setup(mng)

    notify_admins(mng.bot, 'bot started')
    mng.start()
    notify_admins(mng.bot, 'bot stopped')
