from datetime import datetime

from aiogram.types import Message
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from lib.bot import BotManager

from services.notion_api import Database

tasks = Database("67f38400c29f4137ac285fe6569567e2")


class FSM(StatesGroup):
    start = State()
    name = State()
    subject = State()
    deadline = State()
    finish = State()


async def add(message: Message, state: FSMContext):
    await state.set_state(FSM.name)
    await message.answer('Вы пытаетесь добавить строчку в базу заданий')
    await message.answer('Отправьте мне название задачи')
    global row
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
    except(Exception):
        await state.set_state(FSM.deadline)
        await message.answer('Дата некорректна [01.01.1970]')


def setup(mng: BotManager):
    mng.add_state_handler(FSM.start, add)
    mng.add_state_handler(FSM.name, get_name)
    mng.add_state_handler(FSM.subject, get_subject)
    mng.add_state_handler(FSM.deadline, get_deadline)
