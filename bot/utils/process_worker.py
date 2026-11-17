import asyncio
import multiprocessing
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from typing import Any


class ProcessWorker:
    """One reusable worker, with at most one submitted payload even on cancellation."""

    def __init__(self) -> None:
        self._pool: ProcessPoolExecutor | None = None
        self._lock = asyncio.Lock()
        self._pending: asyncio.Task[Any] | None = None
        self._closing: asyncio.Task[None] | None = None

    async def run[T](self, function: Callable[..., T], *args: Any) -> T:
        async with self._lock:
            if self._closing is not None:
                raise RuntimeError("Process worker is closed")
            if self._pending is not None:
                # A cancelled caller cannot cancel a running process job. Drain it
                # before submitting another body instead of queuing large payloads.
                await asyncio.wait([self._pending])
            if self._closing is not None:
                raise RuntimeError("Process worker is closed")
            pending = asyncio.create_task(
                asyncio.to_thread(self._execute, function, *args)
            )
            self._pending = pending
            pending.add_done_callback(self._finished)
            return await asyncio.shield(pending)

    async def start(self) -> None:
        await self.run(bytes)

    def _execute[T](self, function: Callable[..., T], *args: Any) -> T:
        # Pool creation, first spawn, and IPC submission must also stay off-loop.
        if self._pool is None:
            self._pool = ProcessPoolExecutor(
                max_workers=1, mp_context=multiprocessing.get_context("spawn")
            )
        try:
            return self._pool.submit(function, *args).result()
        except BrokenProcessPool:
            self._shutdown()
            raise

    def _finished(self, pending: asyncio.Task[Any]) -> None:
        # Retrieve errors even when the requesting task has already been cancelled.
        if not pending.cancelled():
            pending.exception()
        if self._pending is pending:
            self._pending = None

    async def close(self) -> None:
        if self._closing is None:
            self._closing = asyncio.create_task(self._close())
        # Cleanup continues if the shutdown caller is cancelled.
        await asyncio.shield(self._closing)

    async def _close(self) -> None:
        async with self._lock:
            if self._pending is not None:
                await asyncio.wait([self._pending])
            await asyncio.to_thread(self._shutdown)

    def _shutdown(self) -> None:
        if self._pool is not None:
            self._pool.shutdown(wait=True, cancel_futures=True)
            self._pool = None
