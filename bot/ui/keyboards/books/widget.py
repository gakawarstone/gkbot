from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.books import Book

from .base import BaseMarkup
from .edit_properties import PropertiesMarkup
from .types import _BookProperties, _Events


class WidgetMarkup(BaseMarkup):
    prefix = "book"
    events = _Events

    @classmethod
    def get_book_widget(cls, book: Book) -> InlineKeyboardMarkup:
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text="Прогресс:",
                        callback_data=(
                            f"{PropertiesMarkup.prefix}:"
                            f"{_BookProperties.PROGRESS.value.name_in_db}:"
                            f"{book.id!s}"
                        ),
                    ),
                    InlineKeyboardButton(
                        text="-",
                        callback_data=cls._gen_callback_data(
                            cls.events.decrement, str(book.id)
                        ),
                    ),
                    InlineKeyboardButton(
                        text="+",
                        callback_data=cls._gen_callback_data(
                            cls.events.increment, str(book.id)
                        ),
                    ),
                ],
            ]
        ).as_markup()
