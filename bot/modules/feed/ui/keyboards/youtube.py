from aiogram.utils.keyboard import InlineKeyboardBuilder

from ui.buttons.download import DownloadAction
from ui.buttons.youtube.download import (
    YoutubeDownloadButtonBuilder,
    YoutubeDownloadButtonCallbackData,
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
                        YoutubeDownloadButtonCallbackData(
                            action=DownloadAction.audio,
                            use_callback_message_as_status=False,
                            yt_video_code=yt_code,
                        ),
                    ),
                    YoutubeDownloadButtonBuilder.build(
                        YoutubeDownloadButtonCallbackData(
                            action=DownloadAction.video,
                            use_callback_message_as_status=False,
                            yt_video_code=yt_code,
                        ),
                    ),
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
