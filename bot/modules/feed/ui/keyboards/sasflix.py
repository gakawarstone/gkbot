from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ui.buttons.sasflix import (
    SasflixDownloadButtonBuilder,
    SasflixDownloadButtonCallbackData,
)

from . import BaseFeedMarkup, FeedMarkupButtons, FeedMarkupData


class SasflixFeedItemMarkup(BaseFeedMarkup):
    buttons = FeedMarkupButtons
    data = FeedMarkupData

    @classmethod
    def get_item_markup(cls, item_id: int, topic_uuid: str) -> InlineKeyboardMarkup:
        return InlineKeyboardBuilder(
            [
                [
                    SasflixDownloadButtonBuilder.build(
                        SasflixDownloadButtonCallbackData(topic_uuid)
                    )
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
