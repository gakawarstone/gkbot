from aiogram import Router, F
from aiogram.filters import and_f

from filters.bot_admin import BotAdmin
from .callbacks import PiokokCorouselWidgetEventHandler, PiokokFeedItemMarkup
from .view import PiokokFeedItemView

__all__ = ("PiokokFeedItemView",)


def setup(r: Router):
    r.callback_query.register(
        PiokokCorouselWidgetEventHandler,
        and_f(
            F.data.startswith(PiokokFeedItemMarkup.prefix),
            BotAdmin(),
        ),
    )
