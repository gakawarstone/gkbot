from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.books import Book
from .base import BaseMarkup
from .types import _Events, _BookProperties
from .edit_properties import PropertiesMarkup


class WidgetMarkup(BaseMarkup):
    prefix = 'book'
    events = _Events

    @classmethod
    def get_book_widget(cls, book: Book) -> InlineKeyboardMarkup:
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text='Прогресс:',
                        callback_data=(
                            f'{PropertiesMarkup.prefix}:'
                            f'{_BookProperties.PROGRESS.value.name_in_db}:'
                            f'{book.id}'
                        )
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
