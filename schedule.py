import asyncio
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

    def do_at(self, func, time):
        '''
        Decorator for function
        @{Schedule}.do_at()
        '''
        async def task():
            now = datetime.datetime.now().strftime('%d.%m.%Y_%H:%M')
            if time == now:
                await func()
        self.tasks.append(task)

    async def scheduler(self, delay=5):
        while True:
            for task in self.tasks:
                await task()
            await asyncio.sleep(delay)

    async def on_startup(self, dp):
        asyncio.create_task(self.scheduler())


# bot handlers
async def init(message: aiogram.types.Message):
    await message.answer('Write your remind name')
    bot.add_state_handler(FSM.get_name, get_name)
    await FSM.get_name.set()


async def get_name(message: aiogram.types.Message, state: FSMContext):
    await state.finish()
    data.append(message.text)
    await message.answer('Updated')


class FSM(StatesGroup):
    get_name = State()


# test functions
async def print_time():
    print(datetime.datetime.now())


async def send_data():
    for text in data:
        await bot.send_message(manage.admins[0], text)


if __name__ == '__main__':
    sch = Schedule()
    sch.do_at(send_data, '28.12.2021_17:46')
    bot.add_task(sch.on_startup)
    bot.add_command_handler('set', init)
    bot.start()
