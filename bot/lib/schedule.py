import asyncio
from datetime import datetime, timezone, timedelta
from typing import Awaitable, Any

from lib.meta import MetaSingleton


class Task:
    def __init__(self, func, args=None) -> None:
        self.__func = func
        self.__args = args
        self.time = None

    async def run(self) -> None:
        if self.__args:
            await self.__func(*self.__args)
        else:
            await self.__func()

    @staticmethod
    def create(func: Awaitable, args: list[Any] = None) -> object:
        task = Task(func, args)
        return task

    def at(self, time: datetime) -> object:
        self.time = time
        return self


class Dispatcher:
    async def __dispatcher(self, delay=5):
        while True:
            print('hi')
            await asyncio.sleep(delay)

    async def on_startup(self, dp):
        asyncio.create_task(self.__dispatcher())


class Schedule(Dispatcher, metaclass=MetaSingleton):
    def __init__(self):
        self.tasks = []

    def add_task(self, task: Task):
        self.tasks.append(task)

    async def __check_if_task_now(self, tz=6.0):
        timezone_offset = tz
        tzinfo = timezone(timedelta(hours=timezone_offset))
        for task in self.tasks:
            now = datetime.strftime(datetime.now(tzinfo), '%d.%m.%Y_%H:%M')
            time = datetime.strftime(task.time, '%d.%m.%Y_%H:%M')
            if time == now:
                await task.run()
                self.tasks.remove(task)

    async def __dispatcher(self, delay=5):
        while True:
            await self.__check_if_task_now()
            await asyncio.sleep(delay)

    async def on_startup(self, dp):
        asyncio.create_task(self.__dispatcher())
