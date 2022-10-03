from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from models.books import Book
from ..states import FSM


async def init(message: Message, state: FSMContext):
    await state.set_state(FSM.get_new_book_name)
    await message.answer('Вы пытаетесь добавить книгу. Введите название')


async def get_new_book_name(message: Message, state: FSMContext, data: dict):
    await state.set_state(FSM.get_new_book_author)
    data['book_name'] = message.text
    await message.answer('Автор?')


async def get_new_book_author(message: Message, state: FSMContext, data: dict):
    await state.set_state(FSM.get_new_book_chapters_cnt)
    data['book_author'] = message.text
    await message.answer('кол-во глав?')


async def get_new_book_chapters_cnt(message: Message, state: FSMContext, data: dict):
    await state.set_state(FSM.check_menu_command)
    _, is_created = await Book.get_or_create(
        name=data['book_name'],
        author=data['book_author'],
        chapters_cnt=int(message.text),
        user_id=message.from_user.id
    )
    if not is_created:
        await message.answer('Такая уже есть')
    else:
        await message.answer('Книга добавлена')


def setup(r: Router):
    r.message.register(
        get_new_book_name, StateFilter(state=FSM.get_new_book_name)
    )
    r.message.register(
        get_new_book_author, StateFilter(state=FSM.get_new_book_author)
    )
    r.message.register(
        get_new_book_chapters_cnt,
        StateFilter(state=FSM.get_new_book_chapters_cnt)
    )
