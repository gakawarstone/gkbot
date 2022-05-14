from unittest import mock
from lib.bot import Bot
from bot_config import BOT_TOKEN
from bot_config import bot


def get_bot() -> Bot:
    return Bot(BOT_TOKEN)


def test_bot_create():
    get_bot()


def test_add_message_handler():
    handler = mock.MagicMock()
    bot.add_message_handler(handler)
