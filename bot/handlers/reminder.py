from datetime import datetime

import aiogram
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import Message

from settings import bot
from services.reminder import Reminder
from components.remind_creator import RemindCreator

# [ ] add menu set repeatable notifications


async def add(message: aiogram.types.Message, data: dict):
    await message.delete()
    remind_creator = RemindCreator(message.from_user.id)
    data['rc'] = remind_creator

    await remind_creator.init()

    bot.add_state_handler(FSM.get_mes, get_mes)
    await FSM.get_mes.set()


async def get_mes(message: aiogram.types.Message, state: FSMContext,
                  data: dict):
    await state.finish()
    await message.delete()
    data['text'] = message.text
    remind_creator: RemindCreator = data['rc']

    await remind_creator.set_remind_text(message.text)

    bot.add_state_handler(FSM.get_time, get_time)
    await FSM.get_time.set()


async def get_time(message: Message, state: FSMContext, data: dict):
    try:
        await state.finish()
        await message.delete()
        remind_text = data['text']
        remind_creator: RemindCreator = data['rc']

        time = datetime.strptime(message.text, '%d.%m.%Y_%H:%M')
        Reminder.add_remind(message.from_user.id, time, remind_text)

        await remind_creator.set_remind_time(message.text)
        await remind_creator.set_status_finished()
    except(Exception):
        await remind_creator.set_status_message(
            '❌<b>Формат [30.12.2021_10:28]</b>❌')
        await FSM.get_time.set()


class FSM(StatesGroup):
    get_mes = State()
    get_time = State()
