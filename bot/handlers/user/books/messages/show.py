from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from services.books import BookService
from ui.keyboards.books import EventsMarkup
from ..states import FSM


async def show_user_books(message: Message, state: FSMContext):
    await state.set_state(FSM.check_menu_command)
    await message.answer(
        'Ваши книги: ',
        reply_markup=EventsMarkup.get_books_dialog(
            event=EventsMarkup.events.show,
            books=await BookService.get_all_user_books(message.from_user.id)
        )
    )


def setup(r: Router):
    r.message.register(
        show_user_books,
        StateFilter(state=FSM.show_my_books)
    )