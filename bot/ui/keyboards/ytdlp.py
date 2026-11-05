from aiogram.utils.keyboard import InlineKeyboardBuilder

from ui.buttons.delete_message import deleteMessageButton
from ui.buttons.download import DownloadAction
from ui.buttons.youtube.download import (
    YoutubeDownloadButtonBuilder,
    YoutubeDownloadButtonCallbackData,
)


class YtdlpMarkup:
    @classmethod
    def get_download_dialog(cls, yt_code: str):
        return InlineKeyboardBuilder(
            [
                [
                    YoutubeDownloadButtonBuilder.build(
                        YoutubeDownloadButtonCallbackData(
                            action=DownloadAction.audio,
                            use_callback_message_as_status=True,
                            yt_video_code=yt_code,
                        ),
                    ),
                    YoutubeDownloadButtonBuilder.build(
                        YoutubeDownloadButtonCallbackData(
                            action=DownloadAction.video,
                            use_callback_message_as_status=True,
                            yt_video_code=yt_code,
                        ),
                    ),
                    deleteMessageButton,
                ]
            ]
        ).as_markup()
