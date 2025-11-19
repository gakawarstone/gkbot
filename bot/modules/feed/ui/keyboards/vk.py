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
    def get_item_markup(cls, item_id: int, url: str):
        return InlineKeyboardBuilder(
            [
                [
                    VKDownloadButtonBuilder.build(
                        VKDownloadButtonData.audio,
                        VKDownloadButtonCallbackData(url),
                    ),
                    VKDownloadButtonBuilder.build(
                        VKDownloadButtonData.video,
                        VKDownloadButtonCallbackData(url),
                    ),
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
