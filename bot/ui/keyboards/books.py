from dataclasses import dataclass
from enum import Enum
from sys import prefix
from typing import Type
from unicodedata import name

from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.books import Book
from lib.keyboard_builder import KeyboardBuilder


# NOTE enum instead of dataclass
@dataclass
class _Buttons:
    add_new_book = '📘 Добавить книгу'
    my_books = '📚 Мои книги'
    update_book = '✏️ Изменить книгу'
    exit = '🚪 Выйти'


@dataclass
class _Events:
    show = 'show'
    increment = 'inc'
    decrement = 'dec'
    edit = 'edt'


class BookMarkup:
    prefix = 'book'
    buttons = _Buttons
    events = _Events

    menu = KeyboardBuilder.add_keyboard(
        buttons=[
            [buttons.my_books, buttons.add_new_book, buttons.update_book],
            [buttons.exit]
        ]
    )

    @classmethod
    def __gen_callback_data(cls, event: str, book_id: str):
        return f'{cls.prefix}:{event}:{book_id}'

    @classmethod
    def get_books_dialog(cls, event: str, books: list[Book]) -> InlineKeyboardMarkup:
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text=book.name,
                        callback_data=cls.__gen_callback_data(event, book.id)
                    )
                ]
                for book in books
            ]
        ).as_markup()

    @classmethod
    def get_book_dialog(cls, book: Book) -> InlineKeyboardMarkup:
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text='Прогресс:',
                        callback_data='void'
                    ),
                    InlineKeyboardButton(
                        text='-',
                        callback_data=cls.__gen_callback_data(
                            cls.events.decrement, book.id),
                    ),
                    InlineKeyboardButton(
                        text='+',
                        callback_data=cls.__gen_callback_data(
                            cls.events.increment, book.id)
                    )
                ],
            ]
        ).as_markup()


@dataclass
class _BookProperty:
    name_in_db: str
    spell_ru: str
    event_code: str


class _BookProperties(Enum):
    NAME = _BookProperty(
        name_in_db='name',
        spell_ru='Название',
        event_code='ttl'
    )
    AUTHOR = _BookProperty(
        name_in_db='author',
        spell_ru='Автор',
        event_code='aut'
    )
    PROGRESS = _BookProperty(
        name_in_db='current_chapter',
        spell_ru='Прогресс',
        event_code='prg'
    )


class BookEditMarkup:
    prefix_ = 'ebk'
    props: list[_BookProperty] = [p.value for p in _BookProperties]

    @classmethod  # TODO # FiXME type return markup
    def get_edit_properties_dialog(cls, book: Book):
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text=p.spell_ru,
                        callback_data=f'{cls.prefix_}:{p.name_in_db}:{book.id}'
                    )
                ]
                for p in cls.props
            ]
        ).as_markup()
