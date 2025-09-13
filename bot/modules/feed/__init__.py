from aiogram import Router, F
from aiogram.filters import Command, and_f

from filters.bot_admin import BotAdmin
from configs.commands import USER_COMMANDS
from .ui.keyboards import FeedMarkup
from .handlers import add, auth
from .handlers.views import piokok
from .handlers.messages import ShowFeedItemsHandler
from .handlers.callbacks import ItemEventHandler


def setup(r: Router):
    r.message.register(ShowFeedItemsHandler, Command(USER_COMMANDS.feed))
    r.callback_query.register(ItemEventHandler, F.data.startswith(FeedMarkup.prefix))
    piokok.setup(r)
    add.setup(r)
    auth.setup(r)
