from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from ui.keyboards.books import BookMarkup
from services.books import BookService
from .states import FSM
from . import add_book
from . import edit_book


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
            await show_user_books(message, state)
        case BookMarkup.buttons.update_book:
            await edit_book.choose_book(message)
        case BookMarkup.buttons.exit | 'q':
            await state.set_state(FSM.finish)
            await message.answer('Пока', reply_markup=ReplyKeyboardRemove())
        case _:
            await state.set_state(FSM.check_menu_command)


# FIXME move
async def show_user_books(message: Message, state: FSMContext):
    await state.set_state(FSM.check_menu_command)
    await message.answer(
        'Ваши книги: ',
        reply_markup=BookMarkup.get_books_dialog(
            event=BookMarkup.events.show,
            books=await BookService.get_all_user_books(message.from_user.id)
        )
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
        show_user_books,
        StateFilter(state=FSM.show_my_books)
    )
