from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from . import FeedMarkup


class _Buttons:
    delete = "Убрать"
    keep = "Оставить"
    show_prev_media = "<<"
    show_next_media = ">>"


class _Data:
    delete = "del"
    keep = "keep"
    show_prev_media = "pkprev"
    show_next_media = "pknext"


class PiokokFeedMarkup:
    prefix = "piokok"
    buttons = _Buttons
    data = _Data

    @classmethod
    def get_item_markup(cls, item_id: int, media_len: int, media_current_num: int):
        first_row = [
            InlineKeyboardButton(
                text=cls.buttons.show_prev_media,
                callback_data=f"{cls.prefix}:{cls.data.show_prev_media}:{item_id}_{media_current_num}",
            ),
            InlineKeyboardButton(
                text=str(media_current_num + 1),
                callback_data="void",
            ),
            InlineKeyboardButton(
                text=cls.buttons.show_next_media,
                callback_data=f"{cls.prefix}:{cls.data.show_next_media}:{item_id}_{media_current_num}",
            ),
        ]

        if media_current_num == 0:
            first_row.pop(0)

        if media_current_num == media_len - 1:
            first_row.pop(-1)

        return InlineKeyboardBuilder(
            [
                first_row,
                [
                    InlineKeyboardButton(
                        text=cls.buttons.keep,
                        callback_data=f"{FeedMarkup.prefix}:{cls.data.keep}:{item_id}",
                    ),
                    InlineKeyboardButton(
                        text=cls.buttons.delete,
                        callback_data=f"{FeedMarkup.prefix}:{cls.data.delete}:{item_id}",
                    ),
                ],
            ]
        ).as_markup()
