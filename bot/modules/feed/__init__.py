from aiogram import F, Router
from aiogram.filters import Command

from configs.commands import USER_COMMANDS

from .handlers import add, auth
from .handlers.callbacks import ItemEventHandler
from .handlers.messages import ShowFeedItemsHandler
from .ui.keyboards import FeedMarkup


def setup(r: Router):
    r.message.register(ShowFeedItemsHandler, Command(USER_COMMANDS.feed))
    r.callback_query.register(ItemEventHandler, F.data.startswith(FeedMarkup.prefix))
    add.setup(r)
    auth.setup(r)
