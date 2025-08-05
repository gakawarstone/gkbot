from aiogram import Router, F
from aiogram.filters import and_f

from filters.bot_admin import BotAdmin
from .callbacks import PiokokCarouselWidgetEventHandler
from ....ui.keyboards.piokok import PiokokFeedItemMarkup
from .view import PiokokFeedItemView

__all__ = ("PiokokFeedItemView",)


def setup(r: Router):
    r.callback_query.register(
        PiokokCarouselWidgetEventHandler,
        and_f(
            F.data.startswith(PiokokFeedItemMarkup.prefix),
            BotAdmin(),
        ),
    )
