"""Offline /img burst through aiogram polling; see docs/polling-concurrency.md."""

import argparse
import asyncio
import json
import resource
import time
import tracemalloc
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import cast
from unittest.mock import AsyncMock, patch

from aiogram import Bot, Dispatcher
from aiogram.types import BufferedInputFile, InputMediaPhoto, Message, Update, User

from handlers.prompt.generate_image import generate_image
from services.agents.image_prompt_enhancer import ImagePromptEnhancer
from services.http import HttpService


@dataclass
class Metrics:
    active_updates: int = 0
    peak_updates: int = 0
    active_requests: int = 0
    peak_requests: int = 0
    completed: int = 0
    uploaded_bytes: int = 0
    failures: int = 0


async def benchmark(limit: int, count: int, payload_mib: int, delay: float) -> None:
    metrics = Metrics()
    completed = asyncio.Event()
    dispatcher = Dispatcher()
    bot = Bot("12345678:ABCDEF-GHIJKLMNOPQRSTUV")
    payload_size = payload_mib * 1024 * 1024

    async def enhance(prompt: str) -> str:
        metrics.active_requests += 1
        metrics.peak_requests = max(metrics.peak_requests, metrics.active_requests)
        try:
            await asyncio.sleep(delay)
            return prompt
        finally:
            metrics.active_requests -= 1

    async def get_image(url: str) -> bytes:
        metrics.active_requests += 1
        metrics.peak_requests = max(metrics.peak_requests, metrics.active_requests)
        try:
            # A distinct, allocated response per request, held through upload.
            payload = b"x" * payload_size
            await asyncio.sleep(delay)
            return payload
        finally:
            metrics.active_requests -= 1

    @dataclass
    class ImageMessage:
        # Mocks retain uploaded buffers in call history and distort peak memory.
        text: str | None

        async def delete(self) -> None:
            pass

        async def answer_media_group(self, media: list[InputMediaPhoto]) -> None:
            assert len(media) == 4
            for photo in media:
                image = cast(BufferedInputFile, photo.media)
                assert len(image.data) == payload_size
                metrics.uploaded_bytes += len(image.data)
            await asyncio.sleep(delay)

    async def handle(message: Message) -> None:
        metrics.active_updates += 1
        metrics.peak_updates = max(metrics.peak_updates, metrics.active_updates)
        event = cast(Message, ImageMessage(message.text))
        metrics.failures += 1
        try:
            await generate_image(event)
            metrics.failures -= 1
        finally:
            metrics.active_updates -= 1
            metrics.completed += 1
            if metrics.completed == count:
                completed.set()

    async def updates(*args: object, **kwargs: object) -> AsyncIterator[Update]:
        for update_id in range(count):
            yield Update.model_validate(
                {
                    "update_id": update_id,
                    "message": {
                        "message_id": update_id,
                        "date": 0,
                        "chat": {"id": update_id + 1, "type": "private"},
                        "from": {
                            "id": update_id + 1,
                            "is_bot": False,
                            "first_name": "Load",
                        },
                        "text": "/img benchmark",
                    },
                },
                context={"bot": bot},
            )
        # Polling must stay alive until the last task has finished.
        await completed.wait()
        await asyncio.sleep(0)

    dispatcher.message.register(handle)
    user = User(id=bot.id, is_bot=True, first_name="Benchmark")
    try:
        with (
            patch.object(Bot, "me", AsyncMock(return_value=user)),
            patch.object(Dispatcher, "_listen_updates", updates),
            patch.object(ImagePromptEnhancer, "enhance", enhance),
            patch.object(HttpService, "get", get_image),
        ):
            tracemalloc.start()
            started = time.perf_counter()
            async with asyncio.timeout(120):
                await dispatcher.start_polling(
                    bot,
                    handle_signals=False,
                    handle_as_tasks=True,
                    tasks_concurrency_limit=limit,
                )
            elapsed = time.perf_counter() - started
            _, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()
    finally:
        await bot.session.close()

    assert metrics.completed == count and metrics.failures == 0
    assert metrics.uploaded_bytes == count * 4 * payload_size
    assert metrics.peak_updates == min(count, limit)
    assert metrics.peak_requests <= 4 * limit
    print(
        json.dumps(
            {
                "limit": limit,
                "updates": count,
                "response_mib": payload_mib,
                "stage_delay_seconds": delay,
                "elapsed_seconds": round(elapsed, 3),
                "updates_per_second": round(count / elapsed, 2),
                "peak_updates": metrics.peak_updates,
                "peak_requests": metrics.peak_requests,
                "traced_peak_mib": round(peak_memory / 1024**2, 2),
                "process_peak_rss_mib": round(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2
                ),
            }
        )
    )


def positive_int(value: str) -> int:
    result = int(value)
    if result <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return result


def positive_float(value: str) -> float:
    result = float(value)
    if not 0 < result < float("inf"):
        raise argparse.ArgumentTypeError("must be a finite positive number")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=positive_int, default=10)
    parser.add_argument("--updates", type=positive_int, default=40)
    parser.add_argument("--response-mib", type=positive_int, default=5)
    parser.add_argument("--delay", type=positive_float, default=0.05)
    args = parser.parse_args()
    asyncio.run(benchmark(args.limit, args.updates, args.response_mib, args.delay))


if __name__ == "__main__":
    main()
