from aiogram.utils.keyboard import InlineKeyboardBuilder

from ui.buttons.youtube.download import (
    YoutubeDownloadButtonBuilder,
    YoutubeDownloadButtonCallbackData,
    YoutubeDownloadButtonData,
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
                    YoutubeDownloadButtonBuilder.build(
                        YoutubeDownloadButtonData.audio,
                        YoutubeDownloadButtonCallbackData(yt_code),
                    ),
                    YoutubeDownloadButtonBuilder.build(
                        YoutubeDownloadButtonData.video,
                        YoutubeDownloadButtonCallbackData(yt_code),
                    ),
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
