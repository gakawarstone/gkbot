from aiogram.types import Message

from services.repositories.books import BooksRepository
from ui.keyboards.books import EventsMarkup


async def choose_book(message: Message):
    books = await BooksRepository.get_all_user_books(message.from_user.id)
    markup = EventsMarkup.get_books_dialog(EventsMarkup.events.edit, books)
    await message.answer(
        "Выберите книгу которую вы хотите обновить", reply_markup=markup
    )
