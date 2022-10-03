from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.books import Book
from .types import _BookProperty, _BookProperties


class PropertiesMarkup:
    prefix = 'ebk'
    props: list[_BookProperty] = [p.value for p in _BookProperties]

    @classmethod
    def get_edit_properties_dialog(cls, book: Book) -> InlineKeyboardMarkup:
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text=p.spell_ru,
                        callback_data=f'{cls.prefix}:{p.name_in_db}:{book.id}'
                    )
                ]
                for p in cls.props
            ]
        ).as_markup()
