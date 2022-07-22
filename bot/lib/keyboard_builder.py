from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup
from aiogram.types.keyboard_button import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


class KeyboardBuilder:
    def add_keyboard(self, buttons: list[list[str]], hide: bool = True,
                     placeholder: str = None) -> ReplyKeyboardMarkup:
        ''' add telegram keyboard with row of {buttons}'''
        return ReplyKeyboardBuilder(  # NOTE use markup?
            markup=[self.__row_as_buttons(row) for row in buttons]
        ).as_markup(
            resize_keyboard=True,
            one_time_keyboard=hide,
            input_field_placeholder=placeholder
        )

    def __row_as_buttons(row: list[str]) -> list[KeyboardButton]:
        return [KeyboardButton(text=t) for t in row]
