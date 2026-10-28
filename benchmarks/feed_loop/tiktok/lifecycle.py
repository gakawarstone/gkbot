"""Offline callback/delete probe with real YoutubeDL construction and close.

Run with PYTHONPATH=bot and the project's Python environment. No Telegram,
source HTTP, broker, scheduler database, or production cache access is used.
"""

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import socket
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import uvloop
import yt_dlp
from aiogram import Dispatcher
from aiogram.types import CallbackQuery, Chat, Message, User

# Keep deployment configuration and .env out of the offline experiment.
env = ModuleType("configs.env")
env.BROKER_URL = None
env.BOT_TOKEN = "123:offline"
env.ADMIN_IDS = "0"
env.DB_URL = "sqlite://:memory:"
env.API_SERVER_URL = None
env.TELEGRAPH_API_KEY = None
env.YOUTUBE_API_KEY = None
env.OPENROUTER_API_KEY = None
env.NOTION_API_TOKEN = None
sys.modules["configs.env"] = env

from modules.feed.handlers.callbacks import ItemEventHandler
from modules.feed.handlers.views.tiktok import TikTokFeedItemView
from services.cache_dir import CacheDir
from services.ffmpeg import FfmpegService
from services.gkfeed import GkfeedCredentials
from services.gkfeed.api import GkfeedApi
from services.http import HttpService
from services.schedule import Schedule
from services.tiktok import TikTokService
from services.tiktok.extractor import _EXTRACTORS, TikTokInfoExtractor
from services.tiktok.extractor import yt_dlp as extractor_module
from services.tiktok.extractor.snaptik import Snaptik
from services.tiktok.types import InfoVideoTikTok
from services.ytdlp import YtdlpDownloader
from services.ytdlp._options import VideoDownloadOptions
from services.ytdlp.source import DownloadSource

URL = "https://www.tiktok.com/@offline/video/1"
METADATA = {"title": "offline", "duration": 3, "height": 1080, "width": 720}
REPO = Path(__file__).resolve().parents[3]


def baseline_downloader(revision: str) -> type:
    source = subprocess.run(
        ["git", "show", f"{revision}:bot/services/ytdlp/downloader.py"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    name = "services.ytdlp._audit_baseline"
    module = ModuleType(name)
    sys.modules[name] = module
    exec(compile(source, f"git:{revision}:downloader.py", "exec"), module.__dict__)  # noqa: S102
    return module.YtdlpDownloader


async def probe(
    label: str, operation: Any, semaphore: asyncio.Semaphore | None = None
) -> dict[str, Any]:
    loop = asyncio.get_running_loop()
    done = loop.create_future()
    marks: dict[str, Any] = {"label": label}
    query = CallbackQuery(
        id="offline",
        from_user=User(id=1, is_bot=False, first_name="offline"),
        chat_instance="offline",
        message=Message(
            message_id=1, date=datetime.now(UTC), chat=Chat(id=1, type="private")
        ),
    )
    credentials = loop.create_future()
    credentials.set_result(GkfeedCredentials("offline", "offline"))
    handler = SimpleNamespace(event=query, _gkfeed_credentials=credentials)

    async def delete(message: Message, **kwargs: Any) -> bool:
        marks["delete_ms_after_ready"] = (time.perf_counter() - ready_at) * 1000
        return True

    async def callback() -> None:
        marks["dispatch_ms_after_ready"] = (time.perf_counter() - ready_at) * 1000
        try:
            await ItemEventHandler._handle_event(handler, "del", 1)
        finally:
            done.set_result(None)

    async def dispatch() -> None:
        marks["timer_dispatch_ms_after_ready"] = (time.perf_counter() - ready_at) * 1000
        if semaphore is None:
            await callback()
        else:
            await semaphore.acquire()
            await Dispatcher()._process_with_semaphore(callback(), semaphore)

    # Refresh uvloop's cached clock before setting the deadline.
    await asyncio.sleep(0.010)
    ready_at = time.perf_counter() + 0.005
    with patch.object(Message, "delete", delete):
        loop.call_later(0.005, lambda: asyncio.create_task(dispatch()))
        # Let uvloop arm its timer before entering synchronous baseline code.
        await asyncio.sleep(0.001)
        start = time.perf_counter()
        marks["actual_ready_offset_ms"] = (ready_at - start) * 1000
        await operation()
        marks["operation_ms"] = (time.perf_counter() - start) * 1000
        await done
        await asyncio.sleep(0)
    return marks


async def saturated_probe() -> dict[str, Any]:
    """Model polling's acquire-before-launch with ten waiting TikTok updates."""
    semaphore = asyncio.Semaphore(10)
    all_started = asyncio.Event()
    release = asyncio.Event()
    started = 0

    async def get(url: str) -> bytes:
        nonlocal started
        started += 1
        if started == 10:
            all_started.set()
        await release.wait()
        return b"offline video"

    async def finish() -> None:
        await asyncio.sleep(0.050)
        release.set()
        await asyncio.gather(*tasks)

    tasks: list[asyncio.Task[Any]] = []
    with (
        patch.object(
            TikTokInfoExtractor,
            "get_video_info",
            AsyncMock(
                side_effect=lambda url: InfoVideoTikTok(
                    "https://example.invalid/video", None, None, None
                )
            ),
        ),
        patch.object(HttpService, "get", get),
        patch.object(
            FfmpegService, "get_video_metadata", AsyncMock(return_value=METADATA)
        ),
    ):
        for _ in range(10):
            await semaphore.acquire()
            tasks.append(
                asyncio.create_task(
                    Dispatcher()._process_with_semaphore(
                        TikTokService.get_video(URL), semaphore
                    )
                )
            )
        await all_started.wait()
        return await probe("ten_polling_slots_async_wait_50ms", finish, semaphore)


def generated_snaptik_payload(length: int) -> bytes:
    # Generated valid encoding, not a captured production Snaptik response.
    html = '<a href="https://snapxcdn.example.invalid/video.mp4">' + "x" * length
    encoded = "".join(f"{ord(char)}|" for char in html)
    return f'({json.dumps(encoded)}, "", "0123456789|", 0, 10, "")'.encode()


async def main(args: argparse.Namespace) -> None:
    before = baseline_downloader(args.baseline_revision)
    implementations = {"before": before, "after": YtdlpDownloader}
    records: list[dict[str, Any]] = []

    def extract(ydl: Any, url: str, *, download: bool) -> dict[str, Any]:
        assert url == URL and not download
        return METADATA

    def download(ydl: Any, url: str) -> None:
        assert url == URL
        Path(ydl.params["outtmpl"]["default"]).write_bytes(b"offline video")

    async def convert(input_path: str, output_path: str) -> None:
        Path(output_path).write_bytes(b"offline converted video")

    async def sync_stall() -> None:
        # Timer calibration only; this is not a model of source latency.
        time.sleep(0.020)  # noqa: ASYNC251

    async def flow() -> None:
        # Real view -> service -> extractor -> downloader -> FSInputFile -> send
        # boundary. No authorized Telegram send is performed.
        view = SimpleNamespace(_send_video_item=AsyncMock())
        await TikTokFeedItemView._process_tiktok_item(view, SimpleNamespace(link=URL))
        view._send_video_item.assert_awaited_once()

    with (
        tempfile.TemporaryDirectory(prefix="tiktok-lifecycle-") as directory,
        patch.object(CacheDir, "_CacheDir__base_path", directory),
        patch.object(Schedule, "run_task_after", AsyncMock()),
        patch.object(GkfeedApi, "delete_item_by_id", AsyncMock()),
        patch.object(yt_dlp.YoutubeDL, "extract_info", extract),
        patch.object(yt_dlp.YoutubeDL, "download", download),
        patch.object(FfmpegService, "convert_video", convert),
        patch.object(socket.socket, "connect", side_effect=AssertionError("network")),
    ):
        # Cold records include lazy extractor registration in a fresh process.
        selected = implementations[args.cold_mode]
        records.append(
            await probe(
                f"{args.cold_mode}_info_cold",
                lambda: selected._get_info(URL, DownloadSource.TIKTOK),
            )
        )
        output_path = str(Path(directory) / "stub.mp4")
        opts = {**VideoDownloadOptions.tiktok, "outtmpl": output_path}
        for _ in range(args.repetitions):
            records.append(await probe("idle", lambda: asyncio.sleep(0.025)))
            records.append(await probe("sync_sleep_20ms_control", sync_stall))
            for mode, downloader in implementations.items():
                records.append(
                    await probe(
                        f"{mode}_info_warm",
                        partial(downloader._get_info, URL, DownloadSource.TIKTOK),
                    )
                )
                records.append(
                    await probe(
                        f"{mode}_download_warm",
                        partial(
                            downloader._download_file, URL, opts, DownloadSource.TIKTOK
                        ),
                    )
                )
                with patch.object(extractor_module, "YtdlpDownloader", downloader):
                    records.append(await probe(f"{mode}_view_flow_warm", flow))
            for length in (1000, 10000, 100000):
                payload = generated_snaptik_payload(length)
                with (
                    patch(
                        "services.tiktok.extractor.snaptik.HttpService.get",
                        AsyncMock(return_value=b'<input name="token" value="offline">'),
                    ),
                    patch(
                        "services.tiktok.extractor.snaptik.HttpService.post",
                        AsyncMock(return_value=payload),
                    ),
                ):
                    records.append(
                        await probe(
                            f"generated_snaptik_{length}_chars",
                            lambda: Snaptik().get_video_info(URL),
                        )
                    )
        records.append(await saturated_probe())

    summary = {}
    for label in dict.fromkeys(record["label"] for record in records):
        selected_records = [r for r in records if r["label"] == label]
        summary[label] = {"n": len(selected_records)}
        for metric in (
            "actual_ready_offset_ms",
            "operation_ms",
            "timer_dispatch_ms_after_ready",
            "dispatch_ms_after_ready",
            "delete_ms_after_ready",
        ):
            values = [r[metric] for r in selected_records]
            summary[label][metric] = {
                "median": statistics.median(values),
                "max": max(values),
            }
    result = {
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "method": "5ms readiness timer armed with await sleep(1ms) before operation; actual offset recorded",
        "source_sha256": {
            str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                REPO / "bot/services/ytdlp/downloader.py",
                Path(__file__).resolve(),
            )
        },
        "baseline_revision": args.baseline_revision,
        "cold_mode": args.cold_mode,
        "python": sys.version,
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("yt-dlp", "aiogram", "uvloop")
        },
        "extractor_order": [type(source).__name__ for source in _EXTRACTORS],
        "summary": summary,
        "records": records,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline-revision", default="2db43ed99af695c841ed7c29194df88da8d42225"
    )
    parser.add_argument("--cold-mode", choices=("before", "after"), default="before")
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--output", type=Path, required=True)
    uvloop.run(main(parser.parse_args()))
