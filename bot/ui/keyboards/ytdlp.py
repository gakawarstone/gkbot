from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class _Buttons:
    delete = 'Убрать'
    mp3 = 'mp3'


class _Data:
    delete = 'del'
    mp3 = 'ytdlmp3'


class YtdlpMarkup:
    buttons = _Buttons
    data = _Data

    @classmethod
    def get_download_mp3_dialog(cls, user_id: int, message_id: int):
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text=_Buttons.mp3,
                        callback_data=f'{_Data.mp3}:{user_id}:{message_id}'
                    ),
                    InlineKeyboardButton(
                        text=_Buttons.delete,
                        callback_data=_Data.delete
                    )
                ]
            ]
        ).as_markup()
