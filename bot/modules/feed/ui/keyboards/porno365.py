from aiogram.utils.keyboard import InlineKeyboardBuilder

from ui.buttons.download import DownloadAction
from ui.buttons.porno365 import (
    Porno365DownloadButtonBuilder,
    Porno365DownloadButtonCallbackData,
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
                        Porno365DownloadButtonCallbackData(
                            action=DownloadAction.video,
                            use_callback_message_as_status=False,
                            page_url=link,
                        ),
                    ),
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
