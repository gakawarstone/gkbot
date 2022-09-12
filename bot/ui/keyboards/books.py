from dataclasses import dataclass

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.books import Book
from lib.keyboard_builder import KeyboardBuilder


@dataclass
class _Buttons:
    add_new_book = '📘 Добавить книгу'
    my_books = '📚 Мои книги'
    exit = '🚪 Выйти'


@dataclass
class _Events:
    show = 'show'
    increment = 'inc'
    decrement = 'dec'


class BookMarkup:
    buttons = _Buttons
    events = _Events

    menu = KeyboardBuilder.add_keyboard(
        buttons=[
            [_Buttons.my_books, _Buttons.add_new_book],
            [_Buttons.exit]
        ]
    )
    # FIXME markup instead of builder

    @classmethod
    def get_show_books_dialog(cls, books: list[Book]):  # FIXME return
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text=book.name,
                        callback_data=f'book:{cls.events.show}:{book.id}'
                    )
                ]
                for book in books
            ]
        ).as_markup()

    @classmethod
    def get_book_dialog(cls, book: Book):  # FIXME inkmarkup
        return InlineKeyboardBuilder(
            [

                [
                    InlineKeyboardButton(
                        text='Прогресс:',
                        callback_data='void'
                    ),
                    InlineKeyboardButton(
                        text='-',
                        callback_data=f'book:{cls.events.decrement}:{book.id}'
                    ),
                    InlineKeyboardButton(
                        text='+',
                        callback_data=f'book:{cls.events.increment}:{book.id}',
                    )
                ],
            ]
        ).as_markup()
