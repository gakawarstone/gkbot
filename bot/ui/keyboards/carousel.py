from typing import Type

from aiogram.types import InlineKeyboardButton


class CarouselMarkupButtons:
    show_prev_media = "<<"
    show_next_media = ">>"


class CarouselMarkupData:
    show_prev_media = "pkprev"
    show_next_media = "pknext"


class BaseCarouselMarkup[T: CarouselMarkupButtons, S: CarouselMarkupData]:
    prefix: str
    buttons: Type[T]
    data: Type[S]

    @classmethod
    def _get_carousel_navs_row(
        cls, media_current_num: int, media_len: int, callback_data: str
    ) -> list[InlineKeyboardButton]:
        row = [
            InlineKeyboardButton(
                text=cls.buttons.show_prev_media,
                callback_data=f"{cls.prefix}:{cls.data.show_prev_media}:{media_current_num}:{callback_data}",
            ),
            InlineKeyboardButton(
                text=str(media_current_num + 1),
                callback_data="void",
            ),
            InlineKeyboardButton(
                text=cls.buttons.show_next_media,
                callback_data=f"{cls.prefix}:{cls.data.show_next_media}:{media_current_num}:{callback_data}",
            ),
        ]

        if media_current_num == 0:
            row.pop(0)

        if media_current_num == media_len - 1:
            row.pop(-1)

        return row
