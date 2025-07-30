from aiogram.handlers import BaseHandler as _BaseHandler
from aiogram.types import CallbackQuery

from models.books import Book
from services.repositories.books import BooksRepository


class BaseHandler(_BaseHandler[CallbackQuery]):
    async def _parse_callback(self) -> tuple[str, Book]:
        # Check if self.event.data is not None before splitting
        if self.event.data is None:
            raise ValueError("Callback data is None")
        
        _, event, book_id = self.event.data.split(":")
        book = await BooksRepository.get_book_by_id(book_id)
        return event, book
