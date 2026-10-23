from uuid import UUID

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton

PREFIX = "sasflixbtn"


class SasflixDownloadButtonCallbackData(CallbackData, prefix=PREFIX):
    topic_uuid: UUID


class SasflixDownloadButtonBuilder:
    @staticmethod
    def build(callback_data: SasflixDownloadButtonCallbackData) -> InlineKeyboardButton:
        return InlineKeyboardButton(text="Аудио", callback_data=callback_data.pack())
