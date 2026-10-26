from aiogram.types import InlineKeyboardButton

from .download import CallbackIdentifier, VideoDownloadCallbackData

PREFIX = "p365v2"


class Porno365DownloadButtonCallbackData(
    VideoDownloadCallbackData, prefix=PREFIX, sep="|"
):
    page_url: CallbackIdentifier


class Porno365DownloadButtonBuilder:
    @staticmethod
    def build(
        callback_data: Porno365DownloadButtonCallbackData,
    ) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=callback_data.action.label,
            callback_data=callback_data.pack(),
        )
