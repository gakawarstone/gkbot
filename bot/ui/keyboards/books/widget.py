from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.books import Book
from .base import BaseMarkup
from .types import _Events


class WidgetMarkup(BaseMarkup):
    prefix = 'book'
    events = _Events

    @classmethod
    def get_book_widget(cls, book: Book) -> InlineKeyboardMarkup:
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text='Прогресс:',  # [ ] edit progress
                        callback_data='void'
                    ),
                    InlineKeyboardButton(
                        text='-',
                        callback_data=cls._gen_callback_data(
                            cls.events.decrement, book.id),
                    ),
                    InlineKeyboardButton(
                        text='+',
                        callback_data=cls._gen_callback_data(
                            cls.events.increment, book.id)
                    )
                ],
            ]
        ).as_markup()
