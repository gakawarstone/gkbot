from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton

from .download import CallbackIdentifier

PREFIX = "matreshkabtn"


class MatreshkaDownloadButtonCallbackData(CallbackData, prefix=PREFIX):
    video_id: CallbackIdentifier


class MatreshkaDownloadButtonBuilder:
    @staticmethod
    def build(
        callback_data: MatreshkaDownloadButtonCallbackData,
    ) -> InlineKeyboardButton:
        return InlineKeyboardButton(text="Аудио", callback_data=callback_data.pack())
