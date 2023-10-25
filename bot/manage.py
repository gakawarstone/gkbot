from core.bot import BotStarter
from configs import BOT_CONFIG


def start():
    BotStarter(BOT_CONFIG).start()
