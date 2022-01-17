from bot_config import bot, schedule
import aiogram
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import datetime
data = {}


async def add(message: aiogram.types.Message):
    await message.answer('Вы хотите создать напоминание')
    await message.answer('Напоминание придет в этот чат в указанное время')
    await message.answer('Отправьте текст напоминания')
    bot.add_state_handler(FSM.get_mes, get_mes)
    await FSM.get_mes.set()


async def get_mes(message: aiogram.types.Message, state: FSMContext):
    await state.finish()
    data['mes'] = message.text
    await message.answer('Отправьте дату и время')
    bot.add_state_handler(FSM.get_time, get_time)
    await FSM.get_time.set()


async def get_time(message: aiogram.types.Message, state: FSMContext):
    try:
        await state.finish()
        mes = data['mes']
        time = message.text
        datetime.datetime.strptime(time, '%d.%m.%Y_%H:%M')
        task = Task(bot.send_message, [
            message['from']['id'],
            mes])
        schedule.add_task_at(task.run, time)
        await message.answer('Напоминание добавлено')
    except(Exception):
        await message.answer('Формат [30.12.2021_10:28]')
        await FSM.get_time.set()


class Task:
    def __init__(self, func, args=None):
        self.__func = func
        self.__args = args

    async def run(self):
        if self.__args:
            await self.__func(*self.__args)
        else:
            await self.__func()


class FSM(StatesGroup):
    get_mes = State()
    get_time = State()
