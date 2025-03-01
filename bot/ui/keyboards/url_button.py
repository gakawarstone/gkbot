from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class UrlButton:
    @staticmethod
    def create(url: str, text: str = "redirect") -> InlineKeyboardButton:
        return InlineKeyboardButton(text=text, url=url)

    @staticmethod
    def as_markup(url: str, text: str = "redirect") -> InlineKeyboardMarkup:
        button = UrlButton.create(url, text)
        return InlineKeyboardBuilder([[button]]).as_markup()
