import asyncio
import pickle
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Any, Callable
from sqlalchemy import select, delete

from configs import db
from models.tasks import Task as _Model


class Task:
    def __init__(
        self, func: Callable[..., Awaitable], args: list[Any] | None = None
    ) -> None:
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
        async with db.SessionLocal() as session:
            new_task = _Model(callback=callback_dump, datetime=time)
            session.add(new_task)
            await session.commit()

    async def get_all(self) -> list[tuple[Task, datetime, int]]:
        async with db.SessionLocal() as session:
            stmt = select(_Model)
            result = await session.execute(stmt)
            tasks = result.scalars().all()
            return [
                (pickle.loads(i.callback), i.datetime, i.id) for i in tasks
            ]

    async def remove_by_id(self, id: int) -> None:
        async with db.SessionLocal() as session:
            stmt = delete(_Model).where(_Model.id == id)
            await session.execute(stmt)
            await session.commit()


class Schedule:
    __tasks = TasksStorage()

    @classmethod
    async def add_task(cls, task: Task, time: datetime) -> None:
        await cls.__tasks.add(task, time)

    @staticmethod
    def get_local_tz() -> timezone:
        tzinfo = datetime.now(timezone(timedelta(0))).astimezone().tzinfo
        if not isinstance(tzinfo, timezone):
            raise TypeError(f"Expected timezone, got {type(tzinfo)}")
        return tzinfo

    @staticmethod
    def to_local_tz(date_time: datetime) -> datetime:
        return date_time.astimezone(Schedule.get_local_tz())

    @classmethod
    async def run_task_after(cls, task: Task, delay_seconds: int) -> None:
        run_time = cls.to_local_tz(datetime.now() + timedelta(seconds=delay_seconds))
        await cls.add_task(task, run_time)

    @staticmethod
    def __get_now_timestamp() -> float:
        return datetime.strptime(
            datetime.now().strftime("%d.%m.%Y_%H:%M"), "%d.%m.%Y_%H:%M"
        ).timestamp()

    @classmethod
    async def __dispatcher(cls, delay=5) -> None:
        while True:
            for task, time, id in await cls.__tasks.get_all():
                if time.timestamp() <= cls.__get_now_timestamp():
                    await task.run()
                    await cls.__tasks.remove_by_id(id)
            await asyncio.sleep(delay)

    # FIXME: not async
    @classmethod
    async def on_startup(cls):
        asyncio.create_task(cls.__dispatcher())
