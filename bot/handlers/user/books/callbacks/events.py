from typing import Any

from aiogram.types import InlineKeyboardMarkup, Message

from models.books import Book
from services.repositories.books import BooksRepository
from ui.components.books import BookComponent
from ui.keyboards.books import EventsMarkup, WidgetMarkup
from .base import BaseHandler
from ..messages.edit_property.choose_property import choose_property_to_edit


class EventsHandler(BaseHandler):
    async def handle(self) -> Any:
        event, book = await self._parse_callback()
        message = self.event.message

        if message is None or not isinstance(message, Message):
            raise ValueError("Message is not of type Message")

        match event:
            case EventsMarkup.events.show:
                await self.__show_book_widget(book, message)
            case EventsMarkup.events.increment:
                await self.__update_book_widget(
                    book=await BooksRepository.increment_book_current_chapter(book),
                    message=message,
                )
            case EventsMarkup.events.decrement:
                await self.__update_book_widget(
                    book=await BooksRepository.decrement_book_current_chapter(book),
                    message=message,
                )
            case EventsMarkup.events.edit:
                await choose_property_to_edit(message, book)
            case EventsMarkup.events.delete:
                await BooksRepository.delete_book(book)
                await message.answer("Удалено")

    async def __show_book_widget(self, book: Book, message: Message) -> None:
        text, markup = self.__get_widget_data(book)
        await message.answer(text, reply_markup=markup)

    async def __update_book_widget(self, book: Book, message: Message) -> None:
        text, markup = self.__get_widget_data(book)
        await message.edit_text(text, reply_markup=markup)

    @staticmethod
    def __get_widget_data(book: Book) -> tuple[str, InlineKeyboardMarkup]:
        return BookComponent.render(book), WidgetMarkup.get_book_widget(book)
