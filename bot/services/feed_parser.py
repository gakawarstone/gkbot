from collections.abc import Callable
from typing import Any

from utils.process_worker import ProcessWorker

type ParseJob = tuple[Callable[..., Any], tuple[Any, ...]]


def _parse(job: ParseJob) -> Any:
    function, args = job
    return function(*args)


def _warmup() -> None:
    pass


class FeedParser:
    # Keep HTML trees and their garbage collection in one bounded process.
    _worker: ProcessWorker[ParseJob, Any] = ProcessWorker(_parse)

    @classmethod
    async def run[T](cls, function: Callable[..., T], *args: Any) -> T:
        """Run a pure parser returning ready values, never a soup or handler."""
        return await cls._worker.run((function, args))

    @classmethod
    async def on_startup(cls) -> None:
        await cls.run(_warmup)

    @classmethod
    async def on_shutdown(cls) -> None:
        await cls._worker.close()
