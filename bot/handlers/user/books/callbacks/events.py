from typing import Any

from aiogram.types import InlineKeyboardMarkup

from models.books import Book
from services.repositories.books import BooksRepository
from ui.components.books import BookComponent
from ui.keyboards.books import EventsMarkup, WidgetMarkup
from .base import BaseHandler
from ..messages.edit_property.choose_property import choose_property_to_edit


class EventsHandler(BaseHandler):
    async def handle(self) -> Any:
        event, book = await self._parse_callback()

        match event:
            case EventsMarkup.events.show:
                await self.__show_book_widget(book)
            case EventsMarkup.events.increment:
                await self.__update_book_widget(
                    book=await BooksRepository.increment_book_current_chapter(book)
                )
            case EventsMarkup.events.decrement:
                await self.__update_book_widget(
                    book=await BooksRepository.decrement_book_current_chapter(book)
                )
            case EventsMarkup.events.edit:
                await choose_property_to_edit(self.event.message, book)
            case EventsMarkup.events.delete:
                await BooksRepository.delete_book(book)
                await self.event.message.answer("Удалено")

    async def __show_book_widget(self, book: Book) -> None:
        text, markup = self.__get_widget_data(book)
        await self.event.message.answer(text, reply_markup=markup)

    async def __update_book_widget(self, book: Book) -> None:
        text, markup = self.__get_widget_data(book)
        await self.event.message.edit_text(text, reply_markup=markup)

    @staticmethod
    def __get_widget_data(book: Book) -> tuple[str, InlineKeyboardMarkup]:
        return BookComponent.render(book), WidgetMarkup.get_book_widget(book)
