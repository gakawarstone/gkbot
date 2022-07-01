import datetime

import aiogram
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import Message

from settings import bot, schedule
from lib.schedule import Task

data = {}


async def add(message: aiogram.types.Message):
    await message.answer('Вы хотите создать напоминание')
    await message.answer('Напоминание придет в этот чат в указанное время')
    await message.answer('Отправьте текст напоминания')
    bot.add_state_handler(FSM.get_mes, get_mes)
    await FSM.get_mes.set()


async def get_mes(message: aiogram.types.Message, state: FSMContext):
    await state.finish()
    data['text'] = message.text
    await message.answer('Отправьте дату и время')
    bot.add_state_handler(FSM.get_time, get_time)
    await FSM.get_time.set()


async def get_time(message: Message, state: FSMContext):
    try:
        await state.finish()
        text = data['text']
        time = datetime.datetime.strptime(message.text, '%d.%m.%Y_%H:%M')
        task = Task.create(
            bot.send_message,
            [message.from_user.id, text]
        ).at(time)
        schedule.add_task(task)
        await message.answer('Напоминание добавлено')
    except(Exception):
        await message.answer('Формат [30.12.2021_10:28]')
        await FSM.get_time.set()


class FSM(StatesGroup):
    get_mes = State()
    get_time = State()
