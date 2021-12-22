from bot_config import bot
from page import Database
import log
import aiogram
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from datetime import datetime
tasks = Database("https://www.notion.so/gakawarstone/67f38400c29f4137ac285fe6569567e2?v=d7e870b67e4b4becb65132a814f8f7af")


class Form(StatesGroup):
    name = State()
    subject = State()
    deadline = State()
    status = State()


async def add_row(message: aiogram.types.Message):
    await message.answer('Вы пытаетесь добавить строчку в базу заданий')
    await message.answer('Отправьте мне название задачи')
    global row
    row = tasks.add_row()
    bot.add_state_handler(Form.name, get_name)
    bot.add_state_handler(Form.subject, get_subject)
    bot.add_state_handler(Form.deadline, get_deadline)
    await Form.name.set()


async def get_name(message: aiogram.types.Message, state: FSMContext):
    row.name = message.text
    log.write(message.text)
    await message.answer('Отправьте предмет')
    await Form.next()


async def get_subject(message: aiogram.types.Message, state: FSMContext):
    row.subject = message.text
    log.write(message.text)
    await message.answer('Отправьте дедлайн')
    await Form.next()


async def get_deadline(message: aiogram.types.Message, state: FSMContext):
    try:
        row.deadline = datetime.strptime(message.text, "%d.%m.%Y")
        row.status = 'Не начато'
        log.write(message.text)
        await message.answer('Спасибо')
        await state.finish()
    except(Exception):
        await message.answer('Дата некорректна [01.01.1970]')
        await Form.deadline.set()
