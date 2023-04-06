from aiogram.handlers import BaseHandler as _BaseHandler
from aiogram.types import CallbackQuery

from models.books import Book
from services.books import BookService


class BaseHandler(_BaseHandler[CallbackQuery]):
    # @property
    # def state(self):
    #     return self.data['state']
    #
    # # NOTE add book_context flag that allows middleware to send typed books context
    # @property
    # def ctx(self) -> dict:  # FIXME type dict
    #     return self.data['data']

    async def _parse_callback(self) -> tuple[str, Book]:
        _, event, book_id = self.event.data.split(':')
        book = await BookService.get_book_by_id(book_id)
        return event, book
