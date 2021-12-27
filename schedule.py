import asyncio
import aioschedule as schedule
import time
from bot_config import bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import manage

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
    await FSM.send_mes.set()


async def send_mes(message=None):
    await bot.bot.send_message(manage.admins[0], 'test')


async def scheduler():
    schedule.every(10).seconds.do(send_mes)
    while True:
        await schedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(dp):
    asyncio.create_task(scheduler())


class FSM(StatesGroup):
    send_mes = State()


if __name__ == '__main__':
    bot.add_command_handler('sch', init)
    bot.start(on_startup=on_startup)
