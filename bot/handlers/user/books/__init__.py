from lib.bot import BotManager
from . import menu


def setup(mng: BotManager):
    menu.setup(mng)
