from aiogram import Router, F
from aiogram.filters import Command, and_f

from ui.keyboards.feed import FeedMarkup
from filters.bot_admin import BotAdmin
from .._commands import USER_COMMANDS
from . import add
from .views import piokok
from .messages import ShowFeedItemsHandler
from .callbacks import ItemEventHandler


def setup(r: Router):
    r.message.register(
        ShowFeedItemsHandler, and_f(Command(USER_COMMANDS.feed), BotAdmin())
    )
    r.callback_query.register(
        ItemEventHandler, and_f(F.data.startswith(FeedMarkup.prefix), BotAdmin())
    )
    piokok.setup(r)
    add.setup(r)
