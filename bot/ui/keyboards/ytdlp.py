from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class _Buttons:
    delete = "Убрать"
    audio = "Аудио"
    video = "Видео"


class _Data:
    delete = "del"
    mp3 = "ytdlmp3"
    mp4 = "ytdlmp4"


class YtdlpMarkup:
    buttons = _Buttons
    data = _Data

    @classmethod
    def get_download_dialog(cls, user_id: int, message_id: int):
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text=_Buttons.audio,
                        callback_data=f"{_Data.mp3}:{user_id}:{message_id}",
                    ),
                    InlineKeyboardButton(
                        text=_Buttons.video,
                        callback_data=f"{_Data.mp4}:{user_id}:{message_id}",
                    ),
                    InlineKeyboardButton(
                        text=_Buttons.delete, callback_data=_Data.delete
                    ),
                ]
            ]
        ).as_markup()
