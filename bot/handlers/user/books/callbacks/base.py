from aiogram.handlers import BaseHandler as _BaseHandler
from aiogram.types import CallbackQuery

from models.books import Book
from services.repositories.books import BooksRepository


class BaseHandler(_BaseHandler[CallbackQuery]):
    async def _parse_callback(self) -> tuple[str, Book]:
        _, event, book_id = self.event.data.split(":")
        book = await BooksRepository.get_book_by_id(book_id)
        return event, book
