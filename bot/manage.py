from configs.bot_config import BOT_CONFIG
from core.bot import BotStarter


def start():
    BotStarter(BOT_CONFIG).start()
