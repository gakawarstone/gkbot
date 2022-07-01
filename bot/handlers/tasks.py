from datetime import datetime

import aiogram
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from settings import bot
from lib.page import Database

tasks = Database("67f38400c29f4137ac285fe6569567e2")


class Form(StatesGroup):
    name = State()
    subject = State()
    deadline = State()
    status = State()


async def add(message: aiogram.types.Message):
    await message.answer('Вы пытаетесь добавить строчку в базу заданий')
    await message.answer('Отправьте мне название задачи')
    global row
    row = await tasks.add_row()
    bot.add_state_handler(Form.name, get_name)
    bot.add_state_handler(Form.subject, get_subject)
    bot.add_state_handler(Form.deadline, get_deadline)
    await Form.name.set()


async def get_name(message: aiogram.types.Message, state: FSMContext):
    await row.set_name(message.text)
    await message.answer('Отправьте предмет')
    await Form.next()


async def get_subject(message: aiogram.types.Message, state: FSMContext):
    await row.set_select('Subject', message.text)
    await message.answer('Отправьте дедлайн')
    await Form.next()


async def get_deadline(message: aiogram.types.Message, state: FSMContext):
    try:
        deadline = datetime.strptime(message.text, "%d.%m.%Y")
        await row.set_date('Deadline', deadline)
        await row.set_select('Status', 'Не начато')
        await message.answer('Спасибо')
        await state.finish()
    except(Exception):
        await message.answer('Дата некорректна [01.01.1970]')
        await Form.deadline.set()
