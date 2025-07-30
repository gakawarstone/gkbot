from aiogram.utils.keyboard import InlineKeyboardBuilder

from ui.buttons.youtube.download import (
    YoutubeDownloadButtonBuilder,
    YoutubeDownloadButtonCallbackData,
    YoutubeDownloadButtonData,
)
from ui.buttons.delete_message import deleteMessageButton


class YtdlpMarkup:
    @classmethod
    def get_download_dialog(cls, yt_code: str):
        return InlineKeyboardBuilder(
            [
                [
                    YoutubeDownloadButtonBuilder.build(
                        YoutubeDownloadButtonData.audio,
                        YoutubeDownloadButtonCallbackData(yt_code, True),
                    ),
                    YoutubeDownloadButtonBuilder.build(
                        YoutubeDownloadButtonData.video,
                        YoutubeDownloadButtonCallbackData(yt_code, True),
                    ),
                    deleteMessageButton,
                ]
            ]
        ).as_markup()
