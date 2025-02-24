from typing import Type

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class FeedMarkupButtons:
    delete = "Убрать"
    keep = "Оставить"
    show_all_feed = "Похожие"


class FeedMarkupData:
    delete = "del"
    keep = "keep"
    show_all_feed = "show_all_feed"


class BaseFeedMarkup[T: FeedMarkupButtons, S: FeedMarkupData]:
    prefix = str
    buttons: Type[T]
    data: Type[S]

    @classmethod
    def _get_feed_buttons_row(cls, item_id: int) -> list[InlineKeyboardButton]:
        return [
            InlineKeyboardButton(
                text=cls.buttons.keep,
                callback_data=f"{cls.prefix}:{cls.data.keep}:{item_id}",
            ),
            InlineKeyboardButton(
                text=cls.buttons.delete,
                callback_data=f"{cls.prefix}:{cls.data.delete}:{item_id}",
            ),
        ]


class FeedMarkup(BaseFeedMarkup[FeedMarkupButtons, FeedMarkupData]):
    prefix = "fd"
    buttons = FeedMarkupButtons
    data = FeedMarkupData

    @classmethod
    def get_item_markup(cls, item_id: int, feed_id: int):
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text=cls.buttons.show_all_feed,
                        callback_data=f"{cls.prefix}:{cls.data.show_all_feed}:{feed_id}",
                    ),
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
