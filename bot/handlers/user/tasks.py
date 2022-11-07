from datetime import datetime

from aiogram import Router
from aiogram.filters.state import State, StateFilter, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command

from services.notion_api import Database
from ._commands import USER_COMMANDS

tasks = Database("67f38400c29f4137ac285fe6569567e2")


class FSM(StatesGroup):  # NOTE SG?
    start = State()
    name = State()
    subject = State()
    deadline = State()
    finish = State()


async def add(message: Message, state: FSMContext):
    await state.set_state(FSM.name)
    await message.answer('Вы пытаетесь добавить строчку в базу заданий')
    await message.answer('Отправьте мне название задачи')
    global row  # FIXME use user data middleware
    row = await tasks.add_row()


async def get_name(message: Message, state: FSMContext):
    await state.set_state(FSM.subject)
    await row.set_name(message.text)
    await message.answer('Отправьте предмет')


async def get_subject(message: Message, state: FSMContext):
    await state.set_state(FSM.deadline)
    await row.set_select('Subject', message.text)
    await message.answer('Отправьте дедлайн')


async def get_deadline(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    try:
        deadline = datetime.strptime(message.text, "%d.%m.%Y")
        await row.set_date('Deadline', deadline)
        await row.set_select('Status', 'Не начато')
        await message.answer('Спасибо')
    except (Exception):
        await state.set_state(FSM.deadline)
        await message.answer('Дата некорректна [01.01.1970]')


def setup(r: Router):
    r.message.register(add, StateFilter(state=FSM.start))
    r.message.register(get_name, StateFilter(state=FSM.name))
    r.message.register(get_subject, StateFilter(state=FSM.subject))
    r.message.register(get_deadline, StateFilter(state=FSM.deadline))
    r.message.register(add, Command(commands=USER_COMMANDS.add_tasks))
