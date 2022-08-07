from lib.bot import BotManager
from . import updates, subs


def setup(mng: BotManager):
    updates.setup(mng)
    subs.setup(mng)
