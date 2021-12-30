import asyncio
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import aiogram
import manage
from datetime import datetime, timezone, timedelta
# ADD DATABASE and read data from it


class Schedule:
    def __init__(self):
        self.tasks = []

    def add_task_at(self, func, time):
        task = [func, time]
        self.tasks.append(task)
        print('task added at', task[1])

    async def __dispatcher(self, delay=5, tz=6.0):
        while True:
            timezone_offset = tz
            tzinfo = timezone(timedelta(hours=timezone_offset))
            for task in self.tasks:
                now = datetime.now(tzinfo).strftime('%d.%m.%Y_%H:%M')
                time = task[1]
                if time == now:
                    func = task[0]
                    await func()
                    self.tasks.remove(task)
            await asyncio.sleep(delay)

    async def on_startup(self, dp):
        asyncio.create_task(self.__dispatcher())
