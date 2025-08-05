from datetime import datetime

from aiogram import Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command

from services.notion_api import Database
from configs.commands import USER_COMMANDS

tasks = Database("67f38400c29f4137ac285fe6569567e2")


# NOTE: Fixed by using llm for linting code style issues needs to be rewritten
class TaskStates(StatesGroup):
    name = State()
    subject = State()
    deadline = State()
    finish = State()


async def add(message: Message, state: FSMContext):
    await state.set_state(TaskStates.name)
    await message.answer("Вы пытаетесь добавить строчку в базу заданий")
    await message.answer("Отправьте мне название задачи")
    # Create a new row and store it in the FSM context
    row = await tasks.add_row()
    await state.update_data(row=row)


async def get_name(message: Message, state: FSMContext):
    await state.set_state(TaskStates.subject)
    if message.text is not None:
        # Retrieve the row from the FSM context
        user_data = await state.get_data()
        row = user_data.get("row")
        if row:
            await row.set_name(message.text)
    await message.answer("Отправьте предмет")


async def get_subject(message: Message, state: FSMContext):
    await state.set_state(TaskStates.deadline)
    if message.text is not None:
        # Retrieve the row from the FSM context
        user_data = await state.get_data()
        row = user_data.get("row")
        if row:
            await row.set_select("Subject", message.text)
    await message.answer("Отправьте дедлайн")


async def get_deadline(message: Message, state: FSMContext):
    await state.set_state(TaskStates.finish)
    if message.text is None:
        await state.set_state(TaskStates.deadline)
        await message.answer("Дата некорректна [01.01.1970]")
        return

    try:
        deadline = datetime.strptime(message.text, "%d.%m.%Y")
        # Retrieve the row from the FSM context
        user_data = await state.get_data()
        row = user_data.get("row")
        if row:
            await row.set_date("Deadline", deadline)
            await row.set_select("Status", "Не начато")
        await message.answer("Спасибо")
    except Exception:
        await state.set_state(TaskStates.deadline)
        await message.answer("Дата некорректна [01.01.1970]")


def setup(r: Router):
    r.message.register(add, Command(commands=USER_COMMANDS.add_tasks))
    r.message.register(get_name, StateFilter(TaskStates.name))
    r.message.register(get_subject, StateFilter(TaskStates.subject))
    r.message.register(get_deadline, StateFilter(TaskStates.deadline))
