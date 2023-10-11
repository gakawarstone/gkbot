from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from services.repositories.books import BooksRepository
from ui.keyboards.books import EventsMarkup
from ..states import FSM


async def show_user_books(message: Message, state: FSMContext):
    await state.set_state(FSM.check_menu_command)
    await message.delete()
    await message.answer(
        "Ваши книги: ",
        reply_markup=EventsMarkup.get_books_dialog(
            event=EventsMarkup.events.show,
            books=await BooksRepository.get_all_user_books(message.from_user.id),
        ),
    )


def setup(r: Router):
    r.message.register(show_user_books, StateFilter(FSM.show_my_books))
