from aiogram.utils.keyboard import InlineKeyboardBuilder

from ...buttons.youtube import (
    YoutubeDownloadAudioButtonBuilder,
    YoutubeDownloadAudioButtonCallbackData,
    YoutubeDownloadAudioButtonData,
)
from . import BaseFeedMarkup, FeedMarkupButtons, FeedMarkupData


class YoutubeFeedItemMarkup(BaseFeedMarkup):
    # NOTE: denk mal wie es ersetzt werden kann
    buttons = FeedMarkupButtons
    data = FeedMarkupData

    @classmethod
    def get_item_markup(cls, item_id: int, yt_code: str):
        return InlineKeyboardBuilder(
            [
                [
                    YoutubeDownloadAudioButtonBuilder.build(
                        YoutubeDownloadAudioButtonData(),
                        YoutubeDownloadAudioButtonCallbackData(yt_code),
                    )
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
