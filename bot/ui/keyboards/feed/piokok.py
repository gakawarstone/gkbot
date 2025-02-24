from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..corousel import BaseCorouselMarkup, CorouselMarkupButtons, CorouselMarkupData
from . import BaseFeedMarkup, FeedMarkupButtons, FeedMarkupData


class _Buttons(FeedMarkupButtons, CorouselMarkupButtons):
    pass


class _Data(FeedMarkupData, CorouselMarkupData):
    pass


class PiokokFeedItemMarkup(
    BaseFeedMarkup[_Buttons, _Data], BaseCorouselMarkup[_Buttons, _Data]
):
    prefix = "piokok"
    buttons = _Buttons
    data = _Data

    @classmethod
    def get_item_markup(cls, item_id: int, media_len: int, media_current_num: int):
        return InlineKeyboardBuilder(
            [
                cls._get_corousel_navs_row(media_current_num, media_len, str(item_id)),
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
