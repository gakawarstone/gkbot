import asyncio
from collections.abc import Coroutine
from typing import Any


async def wait_for_completion[T](operation: Coroutine[Any, Any, T]) -> T:
    """Delay cancellation until file I/O finishes, so cleanup cannot race it."""
    task = asyncio.create_task(operation)
    cancellation: asyncio.CancelledError | None = None
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError as error:
            if cancellation is None:
                cancellation = error
    result = task.result()
    if cancellation is not None:
        raise cancellation
    return result
