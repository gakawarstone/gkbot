from lib.bot import Bot
from settings import BOT_TOKEN


def get_bot() -> Bot:
    return Bot(BOT_TOKEN)


def test_bot_create():
    get_bot()
