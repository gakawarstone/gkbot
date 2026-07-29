from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ui.buttons.matreshka import (
    MatreshkaDownloadButtonBuilder,
    MatreshkaDownloadButtonCallbackData,
)

from . import BaseFeedMarkup, FeedMarkupButtons, FeedMarkupData


class MatreshkaFeedItemMarkup(BaseFeedMarkup):
    buttons = FeedMarkupButtons
    data = FeedMarkupData

    @classmethod
    def get_item_markup(
        cls,
        item_id: int,
        video_id: str,
    ) -> InlineKeyboardMarkup:
        return InlineKeyboardBuilder(
            [
                [
                    MatreshkaDownloadButtonBuilder.build(
                        MatreshkaDownloadButtonCallbackData(video_id)
                    )
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
