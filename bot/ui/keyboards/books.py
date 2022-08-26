from dataclasses import dataclass

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from lib.keyboard_builder import KeyboardBuilder


@dataclass
class _Buttons:
    add_new_book = '📘 Добавить книгу'
    my_books = '📚 Мои книги'


class BookMarkup:
    buttons = _Buttons

    menu = KeyboardBuilder.add_keyboard(
        buttons=[
            [_Buttons.my_books, _Buttons.add_new_book]
        ]
    )

    @classmethod
    def get_books_dialog(cls, books: list[str]):
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text=book,
                        callback_data='show_test_book'  # FIXME
                    )
                ]
                for book in books
            ]
        ).as_markup()

    @classmethod
    def get_test_book_dialog(cls):
        return InlineKeyboardBuilder(
            [

                [
                    InlineKeyboardButton(
                        text='Прогресс:',
                        callback_data='book'
                    ),
                    InlineKeyboardButton(
                        text='-',
                        callback_data='book_progress-'
                    ),
                    InlineKeyboardButton(
                        text='+',
                        callback_data='book_progress+',
                    )
                ],
                [
                    InlineKeyboardButton(
                        text='Мои книги <<< Pipka',
                        callback_data='book_menu'
                    )
                ],
            ]
        ).as_markup()
