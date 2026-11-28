import asyncio
import gc
import json
import multiprocessing
import threading
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from unittest.mock import Mock

import pytest

from services.gkfeed._decoder import FeedDecoder
from services.gkfeed._types import FeedItemSummary


async def test_worker_reuse_errors_and_cleanup() -> None:
    original_children = {child.pid for child in multiprocessing.active_children()}
    decoder = FeedDecoder()
    try:
        await decoder.start()
        # The decoder must reuse one child instead of spawning one per response.
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
        assert await decoder.decode(payload) == [
            FeedItemSummary(
                7,
                2,
                "https://example.invalid/7",
                "Заголовок",
                "2026-10-26T10:00:00Z",
            )
        ]
        with pytest.raises(json.JSONDecodeError):
            await decoder.decode(b"invalid json")
        with pytest.raises(KeyError, match="items"):
            await decoder.decode(b"{}")
        assert await decoder.decode(b'{"items":[]}') == []
        assert {child.pid for child in multiprocessing.active_children()} == children
    finally:
        await decoder.close()
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

    def blocked_decode(_function: object, payload: bytes) -> list[FeedItemSummary]:
        assert threading.get_ident() != loop_thread
        submissions.append(payload)
        entered.set()
        assert release.wait(5)
        return []

    monkeypatch.setattr(decoder, "_execute", blocked_decode)
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
        retry_close = asyncio.create_task(decoder.close())
        await asyncio.sleep(0)
        assert not retry_close.done()
    finally:
        release.set()
        await decoder.close()
    await retry_close
    assert submissions == [b"first"]
    with pytest.raises(RuntimeError, match="closed"):
        await decoder.decode(b"later")


async def test_cancelled_job_error_is_observed_and_next_decode_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decoder = FeedDecoder()
    entered = threading.Event()
    release = threading.Event()

    def decode(_function: object, payload: bytes) -> list[FeedItemSummary]:
        if payload == b"cancelled":
            entered.set()
            assert release.wait(5)
            raise ValueError("discarded response")
        return []

    monkeypatch.setattr(decoder, "_execute", decode)
    loop = asyncio.get_running_loop()
    previous_handler = loop.get_exception_handler()
    unhandled_errors: list[dict[str, object]] = []
    loop.set_exception_handler(lambda _loop, context: unhandled_errors.append(context))
    task = asyncio.create_task(decoder.decode(b"cancelled"))
    try:
        assert await asyncio.to_thread(entered.wait, 5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        next_decode = asyncio.create_task(decoder.decode(b"next"))
        await asyncio.sleep(0)
        assert not next_decode.done()
        release.set()
        assert await next_decode == []
        gc.collect()
        await asyncio.sleep(0)
        assert not unhandled_errors
    finally:
        release.set()
        await decoder.close()
        loop.set_exception_handler(previous_handler)


async def test_broken_worker_is_disposed_and_next_request_restarts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decoder = FeedDecoder()
    broken_pool = Mock()
    broken_pool.submit.side_effect = BrokenProcessPool("worker exited")
    factory = Mock(
        side_effect=[
            broken_pool,
            ProcessPoolExecutor(
                max_workers=1, mp_context=multiprocessing.get_context("spawn")
            ),
        ]
    )
    monkeypatch.setattr("utils.process_worker.ProcessPoolExecutor", factory)
    try:
        with pytest.raises(BrokenProcessPool):
            await decoder.decode(b'{"items":[]}')
        broken_pool.shutdown.assert_called_once_with(wait=True, cancel_futures=True)
        assert await decoder.decode(b'{"items":[]}') == []
    finally:
        await decoder.close()
