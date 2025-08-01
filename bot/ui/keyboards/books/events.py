from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.books import Book
from .base import BaseMarkup
from .types import _Events


class EventsMarkup(BaseMarkup):
    prefix = "book"
    events = _Events

    @classmethod
    def get_books_dialog(cls, event: str, books: list[Book]) -> InlineKeyboardMarkup:
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text=book.name,
                        callback_data=cls._gen_callback_data(event, str(book.id)),
                    )
                ]
                for book in books
            ]
        ).as_markup()
