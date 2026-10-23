from aiogram.types import InlineKeyboardButton

from ..download import CallbackIdentifier, DownloadCallbackData

PREFIX = "ytbtn"


class YoutubeDownloadButtonCallbackData(DownloadCallbackData, prefix=PREFIX):
    yt_video_code: CallbackIdentifier


class YoutubeDownloadButtonBuilder:
    @staticmethod
    def build(callback_data: YoutubeDownloadButtonCallbackData) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=callback_data.action.label,
            callback_data=callback_data.pack(),
        )
