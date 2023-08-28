import asyncio
from datetime import datetime
from typing import Awaitable, Any, Callable, Tuple
import pickle

from models.tasks import Task as _Model


class Task:
    def __init__(self, func: Callable[..., Awaitable], args: list[Any] = None) -> None:
        self.__func = func
        self.__args = args

    async def run(self) -> None:
        if self.__args:
            await self.__func(*self.__args)
        else:
            await self.__func()


class TasksStorage:
    async def add(self, task: Task, time: datetime) -> None:
        callback_dump = pickle.dumps(task)
        await _Model.create(callback=callback_dump, datetime=time)

    async def get_all(self) -> list[Tuple[Task, datetime]]:
        return [
            (pickle.loads(i.callback), i.datetime)
            for i in await _Model.all()
        ]

    async def remove(self, task: Task, time: datetime) -> None:
        await _Model.filter(datetime=time).first().delete()


class Schedule:
    __tasks = TasksStorage()

    @classmethod
    async def add_task(cls, task: Task, time: datetime) -> None:
        await cls.__tasks.add(task, time)

    @staticmethod
    def __get_now_timestamp() -> float:
        return datetime.strptime(
            datetime.now().strftime('%d.%m.%Y_%H:%M'),
            '%d.%m.%Y_%H:%M'
        ).timestamp()

    @classmethod
    async def __dispatcher(cls, delay=5) -> None:
        while True:
            for task, time in await cls.__tasks.get_all():
                if time.timestamp() <= cls.__get_now_timestamp():
                    await task.run()
                    await cls.__tasks.remove(task, time)
            await asyncio.sleep(delay)

    @classmethod
    async def on_startup(cls):
        asyncio.create_task(cls.__dispatcher())
