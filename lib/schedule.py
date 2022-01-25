import asyncio
from datetime import datetime, timezone, timedelta
from typing import Awaitable, Any


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


class Schedule:
    def __init__(self):
        self.tasks = []

    def add_task(self, task: Task):
        self.tasks.append(task)

    async def __dispatcher(self, delay=5, tz=6.0):
        while True:
            timezone_offset = tz
            tzinfo = timezone(timedelta(hours=timezone_offset))
            for task in self.tasks:
                now = datetime.strftime(datetime.now(tzinfo), '%d.%m.%Y_%H:%M')
                time = datetime.strftime(task.time, '%d.%m.%Y_%H:%M')
                if time == now:
                    await task.run()
                    self.tasks.remove(task)
            await asyncio.sleep(delay)

    async def on_startup(self, dp):
        asyncio.create_task(self.__dispatcher())
