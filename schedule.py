import asyncio
import aioschedule as schedule
import time
from bot_config import bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import aiogram
import manage
import datetime

data = ['test1', 'test2']


class Schedule:
    def __init__(self):
        self.tasks = []

    def add_task(self, func):
        self.tasks.append(func)

    def start(self):
        pass


async def init(message):
    print(message)
    await message.answer('started from schedule check')
    bot.add_state_handler(FSM.send_mes, send_mes)


async def send_mes(message=None, text='test'):
    await bot.send_message(manage.admins[0], text)


async def set_sch(message: aiogram.types.Message):
    await message.answer('Write your remind name')
    bot.add_state_handler(FSM.get_name, get_name)
    await FSM.get_name.set()


async def get_name(message: aiogram.types.Message, state: FSMContext):
    await state.finish()
    data.append(message.text)
    await message.answer('Updated')


class FSM(StatesGroup):
    send_mes = State()
    get_name = State()


# scheduel
async def scheduler():
    while True:
        print(datetime.datetime.now())
        for text in data:
            await send_mes(text=text)
        await asyncio.sleep(20)


async def on_startup(dp):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    bot.add_command_handler('sch', init)
    bot.add_command_handler('set', set_sch)
    bot.start(on_startup=on_startup)
