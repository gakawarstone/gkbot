import asyncio
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool

from ._types import FeedItemSummary


def _decode_items(payload: bytes) -> list[FeedItemSummary]:
    data = json.loads(payload)
    return [
        FeedItemSummary(
            id=raw_item["id"],
            feed_id=raw_item["feed_id"],
            link=raw_item["link"],
            title=raw_item["title"],
            date=raw_item["date"],
        )
        for raw_item in data["items"]
        if raw_item["link"]
    ]


class FeedDecoder:
    """One reusable worker, with at most one submitted payload even on cancellation."""

    def __init__(self) -> None:
        self._pool: ProcessPoolExecutor | None = None
        self._lock = asyncio.Lock()
        self._pending: asyncio.Task[list[FeedItemSummary]] | None = None
        self._closing: asyncio.Task[None] | None = None

    async def start(self) -> None:
        # Spawn and import before polling; decode also supports lazy initialization.
        await self.decode(b'{"items":[]}')

    async def decode(self, payload: bytes) -> list[FeedItemSummary]:
        async with self._lock:
            if self._closing is not None:
                raise RuntimeError("Feed decoder is closed")
            if self._pending is not None:
                # A cancelled caller cannot cancel a running process job. Drain it
                # before submitting another body instead of queuing large payloads.
                await asyncio.wait([self._pending])
            if self._closing is not None:
                raise RuntimeError("Feed decoder is closed")
            pending = asyncio.create_task(asyncio.to_thread(self._decode, payload))
            self._pending = pending
            pending.add_done_callback(self._finished)
            return await asyncio.shield(pending)

    def _decode(self, payload: bytes) -> list[FeedItemSummary]:
        # Pool creation, first spawn, and IPC submission must also stay off-loop.
        if self._pool is None:
            self._pool = ProcessPoolExecutor(
                max_workers=1, mp_context=multiprocessing.get_context("spawn")
            )
        try:
            return self._pool.submit(_decode_items, payload).result()
        except BrokenProcessPool:
            self._shutdown()
            raise

    def _finished(self, pending: asyncio.Task[list[FeedItemSummary]]) -> None:
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
