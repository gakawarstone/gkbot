from aiogram.types import Message

from services.repositories.books import BooksRepository
from ui.keyboards.books.events import EventsMarkup


async def show_list_to_delete(message: Message):
    books = await BooksRepository.get_all_user_books(message.from_user.id)
    markup = EventsMarkup.get_books_dialog(EventsMarkup.events.delete, books)
    await message.answer("Удалить:", reply_markup=markup)
