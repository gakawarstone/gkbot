from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from models.books import Book
from ui.keyboards.books import BookMarkup
from .states import FSM
from . import add_book


async def show_menu(message: Message, state: FSMContext):
    await message.answer(
        'Вас приветсвует новейшая и наполненная фактами книжная полка',
        reply_markup=BookMarkup.menu
    )
    await state.set_state(FSM.check_menu_command)


async def check_menu_command(message: Message, state: FSMContext):
    match message.text:
        case BookMarkup.buttons.add_new_book:
            await add_book.init(message, state)
        case BookMarkup.buttons.my_books:
            await show_my_books(message, state)
        case BookMarkup.buttons.exit | 'q':
            await state.set_state(FSM.finish)
            await message.answer('Пока')
        case _:
            await state.set_state(FSM.check_menu_command)


async def show_my_books(message: Message, state: FSMContext):
    await state.set_state(FSM.check_menu_command)  # FIXME
    books = await Book.filter(user_id=message.from_user.id).all()
    await message.answer(
        'Ваши книги: ',
        reply_markup=BookMarkup.get_show_books_dialog(books)
    )


def setup(r: Router):
    r.message.register(
        show_menu,
        StateFilter(state=FSM.show_menu) | Command(commands=['books'])
    )
    r.message.register(
        check_menu_command,
        StateFilter(state=FSM.check_menu_command)
    )
    r.message.register(
        show_my_books,
        StateFilter(state=FSM.show_my_books)
    )
