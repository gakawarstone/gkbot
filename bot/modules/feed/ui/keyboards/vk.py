from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ui.buttons.vk import (
    VKDownloadButtonBuilder,
    VKDownloadButtonCallbackData,
    VKDownloadButtonData,
)
from utils.vk import parse_vk_reference

from . import BaseFeedMarkup, FeedMarkupButtons, FeedMarkupData


class VKFeedVideoItemMarkup(BaseFeedMarkup):
    buttons = FeedMarkupButtons
    data = FeedMarkupData

    @classmethod
    def get_item_markup(cls, item_id: int, url: str) -> InlineKeyboardMarkup:
        reference = parse_vk_reference(url)
        return InlineKeyboardBuilder(
            [
                [
                    VKDownloadButtonBuilder.build(
                        VKDownloadButtonData.audio,
                        VKDownloadButtonCallbackData(reference),
                    ),
                    VKDownloadButtonBuilder.build(
                        VKDownloadButtonData.video,
                        VKDownloadButtonCallbackData(reference),
                    ),
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
