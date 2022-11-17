from aiogram.types import Message

from services.books import BookService
from ui.keyboards.books import EventsMarkup


async def choose_book(message: Message):
    books = await BookService.get_all_user_books(message.from_user.id)
    markup = EventsMarkup.get_books_dialog(EventsMarkup.events.edit, books)
    await message.answer('Выберите книгу которую вы хотите обновить',
                         reply_markup=markup)
