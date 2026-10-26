import asyncio
import json
import multiprocessing
import threading
from concurrent.futures.process import BrokenProcessPool
from unittest.mock import Mock

import pytest

from services.gkfeed._decoder import FeedDecoder, _decode_items
from services.gkfeed._types import FeedItemSummary


async def test_worker_reuse_errors_and_cleanup() -> None:
    original_children = {child.pid for child in multiprocessing.active_children()}
    decoder = FeedDecoder()
    try:
        await decoder.start()
        pool = decoder._pool
        assert pool is not None
        children = {child.pid for child in multiprocessing.active_children()}
        assert len(children - original_children) == 1
        payload = json.dumps(
            {
                "items": [
                    {
                        "id": 7,
                        "feed_id": 2,
                        "link": "https://example.invalid/7",
                        "title": "Заголовок",
                        "date": "2026-10-26T10:00:00Z",
                        "text": "Discard unexpected text from list responses",
                    },
                    {"link": ""},
                ]
            }
        ).encode()
        assert (
            await decoder.decode(payload)
            == _decode_items(payload)
            == [
                FeedItemSummary(
                    7,
                    2,
                    "https://example.invalid/7",
                    "Заголовок",
                    "2026-10-26T10:00:00Z",
                )
            ]
        )
        with pytest.raises(json.JSONDecodeError):
            await decoder.decode(b"invalid json")
        with pytest.raises(KeyError, match="items"):
            await decoder.decode(b"{}")
        assert await decoder.decode(b'{"items":[]}') == []
        assert decoder._pool is pool
        assert {child.pid for child in multiprocessing.active_children()} == children
    finally:
        await decoder.close()
    assert decoder._pool is None
    assert {
        child.pid for child in multiprocessing.active_children()
    } == original_children
    await decoder.close()
    with pytest.raises(RuntimeError, match="closed"):
        await decoder.decode(b'{"items":[]}')


async def test_cancellation_keeps_one_job_and_shutdown_drains_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decoder = FeedDecoder()
    entered = threading.Event()
    release = threading.Event()
    submissions: list[bytes] = []
    loop_thread = threading.get_ident()

    def blocked_decode(payload: bytes) -> list[FeedItemSummary]:
        assert threading.get_ident() != loop_thread
        submissions.append(payload)
        entered.set()
        assert release.wait(5)
        return []

    monkeypatch.setattr(decoder, "_decode", blocked_decode)
    first = asyncio.create_task(decoder.decode(b"first"))
    try:
        assert await asyncio.to_thread(entered.wait, 5)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        for _ in range(20):
            waiting = asyncio.create_task(decoder.decode(b"waiting"))
            await asyncio.sleep(0)
            waiting.cancel()
            with pytest.raises(asyncio.CancelledError):
                await waiting
        assert submissions == [b"first"]
        closing = asyncio.create_task(decoder.close())
        await asyncio.sleep(0)
        closing.cancel()
        with pytest.raises(asyncio.CancelledError):
            await closing
        assert decoder._closing is not None
        assert not decoder._closing.done()
    finally:
        release.set()
        await decoder.close()
    assert submissions == [b"first"]
    assert decoder._pending is None


async def test_cancelled_job_error_is_observed_and_next_decode_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decoder = FeedDecoder()
    entered = threading.Event()
    release = threading.Event()

    def decode(payload: bytes) -> list[FeedItemSummary]:
        if payload == b"cancelled":
            entered.set()
            assert release.wait(5)
            raise ValueError("discarded response")
        return []

    monkeypatch.setattr(decoder, "_decode", decode)
    task = asyncio.create_task(decoder.decode(b"cancelled"))
    try:
        assert await asyncio.to_thread(entered.wait, 5)
        pending = decoder._pending
        assert pending is not None
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        next_decode = asyncio.create_task(decoder.decode(b"next"))
        await asyncio.sleep(0)
        assert not next_decode.done()
        release.set()
        assert await next_decode == []
        assert pending.done()
        assert not pending._log_traceback
    finally:
        release.set()
        await decoder.close()


async def test_broken_worker_is_disposed_and_next_request_restarts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decoder = FeedDecoder()
    broken_pool = Mock()
    broken_pool.submit.side_effect = BrokenProcessPool("worker exited")
    monkeypatch.setattr(decoder, "_pool", broken_pool)
    try:
        with pytest.raises(BrokenProcessPool):
            await decoder.decode(b'{"items":[]}')
        broken_pool.shutdown.assert_called_once_with(wait=True, cancel_futures=True)
        assert decoder._pool is None
        assert await decoder.decode(b'{"items":[]}') == []
    finally:
        await decoder.close()
