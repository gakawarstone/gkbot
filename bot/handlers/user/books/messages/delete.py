from aiogram.types import Message

from services.books import BookService
from ui.keyboards.books.events import EventsMarkup


async def show_list_to_delete(message: Message):
    books = await BookService.get_all_user_books(message.from_user.id)
    markup = EventsMarkup.get_books_dialog(
        EventsMarkup.events.delete, books)
    await message.answer('Удалить:', reply_markup=markup)
