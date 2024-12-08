from aiogram import Router, F
from aiogram.filters import and_f

from filters.bot_admin import BotAdmin
from ui.keyboards.feed.piokok import PiokokFeedMarkup
from ._callbacks import PiokokCorouselWidgetEventHandler


def setup(r: Router):
    r.callback_query.register(
        PiokokCorouselWidgetEventHandler,
        and_f(F.data.startswith(PiokokFeedMarkup.prefix), BotAdmin()),
    )
