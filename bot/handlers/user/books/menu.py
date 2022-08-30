from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ui.keyboards.books import BookMarkup

router = Router()


class FSM(StatesGroup):
    show_menu = State()
    check_menu_command = State()
    get_new_book_name = State()
    show_my_books = State()
    finish = State()
    show_test_book = State()


@router.message(
    StateFilter(state=FSM.show_menu)
)
@router.message(
    Command(commands=['books'])
)
async def show_menu(message: Message, state: FSMContext):
    await message.answer('HELLO', reply_markup=BookMarkup.menu)
    await state.set_state(FSM.check_menu_command)


@router.message(
    StateFilter(state=FSM.check_menu_command)
)
async def check_menu_command(message: Message, state: FSMContext):
    match message.text:
        case BookMarkup.buttons.add_new_book:
            await state.set_state(FSM.show_menu)
        case BookMarkup.buttons.my_books:
            await show_my_books(message, state)
        case 'q':
            await state.set_state(FSM.finish)
        case _:
            await state.set_state(FSM.show_menu)


@router.message(
    StateFilter(state=FSM.show_my_books)
)
async def show_my_books(message: Message, state: FSMContext):
    await state.set_state(FSM.check_menu_command)
    await message.answer('Ваши книги: ', reply_markup=BookMarkup.get_books_dialog(['pipka']))


@router.callback_query(
    text='show_test_book'
)
async def show_test_book(callback: CallbackQuery, state: FSMContext, data: dict):
    await state.set_state(FSM.check_menu_command)
    data['progress'] = 1
    text = '<u>Название:</u>       <b>pipka</b>\n\n'
    text += '<u>Прогресс(главы):</u>         <b>1</b> из 24'
    await callback.message.answer(
        text,
        reply_markup=BookMarkup.get_test_book_dialog()
    )


@router.callback_query(
    text='book_progress+'
)
async def increment_progress(callback: CallbackQuery, state: FSMContext, data: dict):
    await state.set_state(FSM.check_menu_command)
    data['progress'] += 1
    text = '<u>Название:</u>       <b>pipka</b>\n\n'
    text += f'<u>Прогресс(главы):</u>         <b>{data["progress"]}</b> из 24'
    await callback.message.edit_text(
        text,
        reply_markup=BookMarkup.get_test_book_dialog()
    )


@router.callback_query(
    text='book_progress-'
)
async def decrement_progress(callback: CallbackQuery, state: FSMContext, data: dict):
    await state.set_state(FSM.check_menu_command)
    data['progress'] -= 1
    text = '<b>Название ✍️:</b>                  Pipka\n'
    text += '<b>Автор 👨‍🦳:</b>                         Malenkoy\n'
    text += '<b>Оценка 🗯:</b>                      2.2/10\n'
    text += '<b>Статус :/b> Читаю'
    text += f'<b>Прогресс(главы) 📈:</b>     <b>{data["progress"]}</b> из 24'
    await callback.message.edit_text(
        text,
        reply_markup=BookMarkup.get_test_book_dialog()
    )


@router.message(
    StateFilter(state=FSM.get_new_book_name)
)
async def get_new_book_name(message: Message, state: FSMContext, data: dict):
    await state.set_state(FSM.finish)


def setup(r: Router):
    r.include_router(router)
