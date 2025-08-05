from aiogram import Router
from aiogram.filters import Command, StateFilter, or_f, and_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from ui.static import Images
from filters.not_command import NotCommandFilter
from ui.keyboards.books import MenuMarkup
from configs.commands import USER_COMMANDS
from .messages import delete, show
from .messages.add.start import InitAddBookHandler
from .messages.edit_property.choose_book import choose_book
from .states import FSM


async def show_menu(message: Message, state: FSMContext):
    await message.answer_photo(
        await Images.book_shelf.as_input_file(),
        caption="Вас приветствует новейшая и наполненная фактами книжная полка",
        reply_markup=MenuMarkup.menu,
    )
    await state.set_state(FSM.check_menu_command)


async def check_menu_command(message: Message, state: FSMContext, data: dict):
    match message.text:
        case MenuMarkup.buttons.add_new_book:
            await InitAddBookHandler(message, state=state, data=data)
        case MenuMarkup.buttons.my_books:
            await show.show_user_books(message, state)
        case MenuMarkup.buttons.update_book:
            await choose_book(message)
        case MenuMarkup.buttons.exit | "q":
            await state.set_state(FSM.finish)
            await message.answer("Пока", reply_markup=ReplyKeyboardRemove())
        case MenuMarkup.buttons.delete_book:
            await delete.show_list_to_delete(message)
        case _:
            await state.set_state(FSM.check_menu_command)
            await message.answer("Для выхода введите q")


def setup(r: Router):
    r.message.register(
        show_menu,
        or_f(StateFilter(FSM.show_menu), Command(commands=USER_COMMANDS.books)),
    )
    r.message.register(
        check_menu_command,
        and_f(StateFilter(FSM.check_menu_command), NotCommandFilter()),
    )
