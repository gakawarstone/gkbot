from aiogram.types.keyboard_button import KeyboardButton
from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup


class KeyboardBuilder:
    @classmethod
    def add_keyboard(
        cls,
        buttons: list[list[str]],
        hide: bool = True,
        placeholder: str | None = None,
    ) -> ReplyKeyboardMarkup:
        """add telegram keyboard with row of {buttons}"""
        return ReplyKeyboardMarkup(
            keyboard=[cls.__row_as_buttons(row) for row in buttons],
            resize_keyboard=True,
            one_time_keyboard=hide,
            input_field_placeholder=placeholder,
        )

    @staticmethod
    def __row_as_buttons(row: list[str]) -> list[KeyboardButton]:
        return [KeyboardButton(text=t) for t in row]
