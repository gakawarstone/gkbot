from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class _Buttons:
    stop = 'Стоп'


class TimerMarkup:
    buttons = _Buttons

    @classmethod
    def get_timer_dialog(cls, timer_name: str):
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text=cls.buttons.stop,
                        callback_data=f'stop_timer:{timer_name}'
                    )
                ]
            ]
        ).as_markup()
