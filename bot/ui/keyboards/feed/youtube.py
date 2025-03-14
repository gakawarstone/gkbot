from aiogram.utils.keyboard import InlineKeyboardBuilder

from ui.buttons.youtube.download_audio import (
    YoutubeDownloadAudioButtonBuilder,
    YoutubeDownloadAudioButtonCallbackData,
    YoutubeDownloadAudioButtonData,
)
from ui.buttons.youtube.download_video import (
    YoutubeDownloadVideoButtonBuilder,
    YoutubeDownloadVideoButtonCallbackData,
    YoutubeDownloadVideoButtonData,
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
                    ),
                    YoutubeDownloadVideoButtonBuilder.build(
                        YoutubeDownloadVideoButtonData(),
                        YoutubeDownloadVideoButtonCallbackData(yt_code),
                    ),
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
