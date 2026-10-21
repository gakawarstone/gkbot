from aiogram.utils.keyboard import InlineKeyboardBuilder

from ui.buttons.vk import (
    VKDownloadButtonBuilder,
    VKDownloadButtonCallbackData,
    VKDownloadButtonData,
)
from utils.vk import get_vk_id
from . import BaseFeedMarkup, FeedMarkupButtons, FeedMarkupData


class VKFeedVideoItemMarkup(BaseFeedMarkup):
    buttons = FeedMarkupButtons
    data = FeedMarkupData

    @classmethod
    def get_item_markup(cls, item_id: int, url: str):
        vk_id = get_vk_id(url)
        return InlineKeyboardBuilder(
            [
                [
                    VKDownloadButtonBuilder.build(
                        VKDownloadButtonData.audio,
                        VKDownloadButtonCallbackData(vk_id),
                    ),
                    VKDownloadButtonBuilder.build(
                        VKDownloadButtonData.video,
                        VKDownloadButtonCallbackData(vk_id),
                    ),
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
