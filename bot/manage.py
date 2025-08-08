from core.bot import BotStarter

from configs.bot_config import BOT_CONFIG


def start():
    BotStarter(BOT_CONFIG).start()
