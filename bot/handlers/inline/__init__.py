from lib.bot import BotManager
from . import tiktok


def setup(mng: BotManager):
    tiktok.setup(mng)
