import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Any, Callable, ClassVar
import pickle

from models.tasks import Task as _Model

logger = logging.getLogger(__name__)


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
        await _Model.create(callback=callback_dump, datetime=time)

    async def get_all(self) -> list[tuple[Task, datetime, int]]:
        return [
            (pickle.loads(i.callback), i.datetime, i.id) for i in await _Model.all()
        ]

    async def remove_by_id(self, id: int) -> None:
        [await i.delete() for i in await _Model.filter(id=id).all()]


class Schedule:
    __tasks = TasksStorage()
    __max_task_attempts = 3
    __attempts: ClassVar[dict[int, int]] = {}
    __dispatcher_task: ClassVar[asyncio.Task | None] = None

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
    async def __run_due_tasks(cls) -> None:
        for task, time, id in await cls.__tasks.get_all():
            if time.timestamp() <= cls.__get_now_timestamp():
                try:
                    await task.run()
                except Exception:
                    if cls.__register_failure(id):
                        await cls.__tasks.remove_by_id(id)
                    continue
                cls.__attempts.pop(id, None)
                await cls.__tasks.remove_by_id(id)

    @classmethod
    def __register_failure(cls, id: int) -> bool:
        """Count a failed attempt and return True when the task must be removed."""
        attempts = cls.__attempts.get(id, 0) + 1
        cls.__attempts[id] = attempts
        if attempts >= cls.__max_task_attempts:
            cls.__attempts.pop(id, None)
            logger.exception(
                "Scheduled task %s failed %s times and was removed", id, attempts
            )
            return True
        logger.exception(
            "Scheduled task %s failed, attempt %s/%s", id, attempts, cls.__max_task_attempts
        )
        return False

    @classmethod
    async def __dispatcher(cls, delay: int = 5) -> None:
        while True:
            try:
                await cls.__run_due_tasks()
            except Exception:
                logger.exception("Scheduled tasks pass failed")
            await asyncio.sleep(delay)

    @classmethod
    async def on_startup(cls) -> None:
        cls.__dispatcher_task = asyncio.create_task(cls.__dispatcher())

    @classmethod
    async def on_shutdown(cls) -> None:
        if cls.__dispatcher_task is None:
            return
        cls.__dispatcher_task.cancel()
        try:
            await cls.__dispatcher_task
        except asyncio.CancelledError:
            pass
        cls.__dispatcher_task = None
