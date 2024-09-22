from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class _Buttons:
    delete = "Убрать"
    keep = "Оставить"


class _Data:
    delete = "del"
    keep = "keep"


class FeedMarkup:
    prefix = "fd"
    buttons = _Buttons
    data = _Data

    @classmethod
    def get_item_markup(cls, item_id: int):
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text=cls.buttons.keep,
                        callback_data=f"{cls.prefix}:{cls.data.keep}:{item_id}",
                    ),
                    InlineKeyboardButton(
                        text=cls.buttons.delete,
                        callback_data=f"{cls.prefix}:{cls.data.delete}:{item_id}",
                    ),
                ]
            ]
        ).as_markup()
