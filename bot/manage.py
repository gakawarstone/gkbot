from settings import TASKS_ON_STARTUP, mng
from lib.bot import BotManager
import middlewares
import handlers


def start(mng: BotManager = mng):
    mng.add_tasks_on_startup(TASKS_ON_STARTUP)
    middlewares.setup(mng.dp)
    handlers.setup(mng.dp)
    mng.start()
