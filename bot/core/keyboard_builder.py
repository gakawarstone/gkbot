from aiogram.types.keyboard_button import KeyboardButton
from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


class KeyboardBuilder:
    @classmethod
    def add_keyboard(
        cls,
        buttons: list[list[str]],
        hide: bool = True,
        placeholder: str | None = None,
    ) -> ReplyKeyboardMarkup:
        """add telegram keyboard with row of {buttons}"""
        keyboard = [cls.__row_as_buttons(row) for row in buttons]
        for row in keyboard:
            if len(row) > ReplyKeyboardBuilder.max_width:
                raise ValueError(
                    f"Row {row!r} is too long (max width: {ReplyKeyboardBuilder.max_width})"
                )
        if sum(map(len, keyboard)) > ReplyKeyboardBuilder.max_buttons:
            raise ValueError(
                "Too much buttons detected Max allowed count - "
                f"{ReplyKeyboardBuilder.max_buttons}"
            )
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=hide,
            input_field_placeholder=placeholder,
        )

    @staticmethod
    def __row_as_buttons(row: list[str]) -> list[KeyboardButton]:
        return [KeyboardButton(text=t) for t in row]
