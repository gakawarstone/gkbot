from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class UrlButtonMarkup:
    def get(url: str, text: str = 'redirect') -> InlineKeyboardMarkup:
        return InlineKeyboardBuilder(
            [[InlineKeyboardButton(text=text, url=url)]]
        ).as_markup()
