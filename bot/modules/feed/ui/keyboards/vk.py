from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ui.buttons.vk import (
    VKDownloadButtonBuilder,
    VKDownloadButtonCallbackData,
    VKDownloadButtonData,
)

from . import BaseFeedMarkup, FeedMarkupButtons, FeedMarkupData


class VKFeedVideoItemMarkup(BaseFeedMarkup):
    buttons = FeedMarkupButtons
    data = FeedMarkupData

    @classmethod
    def get_item_markup(cls, item_id: int, video_id: str) -> InlineKeyboardMarkup:
        return InlineKeyboardBuilder(
            [
                [
                    VKDownloadButtonBuilder.build(
                        VKDownloadButtonData.audio,
                        VKDownloadButtonCallbackData(video_id),
                    ),
                    VKDownloadButtonBuilder.build(
                        VKDownloadButtonData.video,
                        VKDownloadButtonCallbackData(video_id),
                    ),
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
