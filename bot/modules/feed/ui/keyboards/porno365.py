from aiogram.utils.keyboard import InlineKeyboardBuilder

from ui.buttons.porno365 import (
    Porno365DownloadButtonBuilder,
    Porno365DownloadButtonCallbackData,
    Porno365DownloadButtonData,
)
from . import BaseFeedMarkup, FeedMarkupButtons, FeedMarkupData


class Porno365FeedItemMarkup(BaseFeedMarkup):
    buttons = FeedMarkupButtons
    data = FeedMarkupData

    @classmethod
    def get_item_markup(cls, item_id: int, link: str):
        return InlineKeyboardBuilder(
            [
                [
                    Porno365DownloadButtonBuilder.build(
                        Porno365DownloadButtonData.video,
                        Porno365DownloadButtonCallbackData(link),
                    ),
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
