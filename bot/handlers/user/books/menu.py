from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from ui.keyboards.books import MenuMarkup
from .messages import add, edit_property, show
from .states import FSM


async def show_menu(message: Message, state: FSMContext):
    await message.answer(
        'Вас приветсвует новейшая и наполненная фактами книжная полка',
        reply_markup=MenuMarkup.menu
    )
    await state.set_state(FSM.check_menu_command)


async def check_menu_command(message: Message, state: FSMContext):
    match message.text:
        case MenuMarkup.buttons.add_new_book:
            await add.init(message, state)
        case MenuMarkup.buttons.my_books:
            await show.show_user_books(message, state)
        case MenuMarkup.buttons.update_book:
            await edit_property.choose_book(message)
        case MenuMarkup.buttons.exit | 'q':
            await state.set_state(FSM.finish)
            await message.answer('Пока', reply_markup=ReplyKeyboardRemove())
        case _:
            await state.set_state(FSM.check_menu_command)


def setup(r: Router):
    r.message.register(
        show_menu,
        StateFilter(state=FSM.show_menu) | Command(commands=['books'])
    )
    r.message.register(
        check_menu_command,
        StateFilter(state=FSM.check_menu_command)
    )
