from aiogram import Router, F
from aiogram.filters import Command, and_f

from ui.keyboards.feed import FeedMarkup
from filters.bot_admin import BotAdmin
from .._commands import USER_COMMANDS
from . import piokok
from .messages import GetFeedItemHandler
from .callbacks import ItemEventHandler


def setup(r: Router):
    r.message.register(
        GetFeedItemHandler, and_f(Command(USER_COMMANDS.feed), BotAdmin())
    )
    r.callback_query.register(
        ItemEventHandler, and_f(F.data.startswith(FeedMarkup.prefix), BotAdmin())
    )
    piokok.setup(r)
