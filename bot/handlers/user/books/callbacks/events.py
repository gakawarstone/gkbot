from typing import Any

from aiogram.types import InlineKeyboardMarkup

from models.books import Book
from services.books import BookService
from ui.components.books import BookComponent
from ui.keyboards.books import BookMarkup  # FIXME EventsMarkup
from .. import edit_book
from .base import BaseHandler


class EventsHandler(BaseHandler):
    async def handle(self) -> Any:
        event, book = await self._parse_callback()

        match event:
            case BookMarkup.events.show:
                await self.__show_book_widget(book)
            case BookMarkup.events.increment:
                await self.__update_book_widget(
                    book=BookService.increment_book_current_chapter(book)
                )
            case BookMarkup.events.decrement:
                await self.__update_book_widget(
                    book=BookService.decrement_book_current_chapter(book)
                )
            case BookMarkup.events.edit:
                await edit_book.choose_property_to_edit(
                    self.event.message, book)

    async def __show_book_widget(self, book: Book) -> None:
        text, markup = self.__get_widget_data(book)
        await self.event.message.answer(text, reply_markup=markup)

    async def __update_book_widget(self, book: Book) -> None:
        text, markup = self.__get_widget_data(book)
        await self.event.message.edit_text(text, reply_markup=markup)

    def __get_widget_data(self,
                          book: Book) -> tuple[str, InlineKeyboardMarkup]:
        return BookComponent.render(book), BookMarkup.get_book_dialog(book)
