"""Offline DataJob construction, fallback and callback/delete readiness probe.

Run the whole series under flock; see README.md. Each cold record comes from
a fresh Python process. Telegram delete and feed API calls are local stubs.
"""

import argparse
import asyncio
import importlib.metadata
import json
import socket
import statistics
import subprocess
import sys
import threading
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from types import MethodType, ModuleType, SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, patch

import uvloop
from aiogram.types import CallbackQuery, Chat, Message, User
from gallery_dl.job import DataJob
from requests import Response

# Do not load deployment configuration or .env in this offline experiment.
env = ModuleType("configs.env")
for key, value in {
    "BOT_TOKEN": "123:offline",
    "ADMIN_IDS": "0",
    "DB_URL": "sqlite://:memory:",
    "BROKER_URL": None,
    "API_SERVER_URL": None,
    "TELEGRAPH_API_KEY": None,
    "YOUTUBE_API_KEY": None,
    "OPENROUTER_API_KEY": None,
    "NOTION_API_TOKEN": None,
}.items():
    setattr(env, key, value)
sys.modules["configs.env"] = env

import services.tiktok.extractor.gallery_dl as fallback_module
from modules.feed.handlers.callbacks import ItemEventHandler
from services.gallery_dl import GalleryDlService
from services.gkfeed import GkfeedCredentials
from services.gkfeed.api import GkfeedApi
from services.http import HttpService
from services.tiktok.extractor import _EXTRACTORS, TikTokInfoExtractor
from services.tiktok.extractor.exceptions import SourceInfoExtractFailed

URL = "https://www.tiktok.com/@offline/video/1"
REPO = Path(__file__).resolve().parents[3]
BASELINE = "2db43ed99af695c841ed7c29194df88da8d42225"


def baseline_service(revision: str) -> type[GalleryDlService]:
    source = subprocess.run(
        ["git", "show", f"{revision}:bot/services/gallery_dl.py"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    module = ModuleType("services._gallery_audit_baseline")
    sys.modules[module.__name__] = module
    # Load the exact read-only baseline, without changing the working checkout.
    exec(compile(source, f"git:{revision}:gallery_dl.py", "exec"), module.__dict__)  # noqa: S102
    return module.__dict__["GalleryDlService"]


async def probe(label: str, operation: Callable[[], Awaitable[Any]]) -> dict[str, Any]:
    loop = asyncio.get_running_loop()
    done: asyncio.Future[None] = loop.create_future()
    callback_tasks: list[asyncio.Task[None]] = []
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
    handler = cast(
        ItemEventHandler,
        SimpleNamespace(event=query, _gkfeed_credentials=credentials),
    )

    async def delete(message: Message, **kwargs: Any) -> bool:
        marks["delete_ms_after_ready"] = (time.perf_counter() - ready_at) * 1000
        return True

    async def callback() -> None:
        marks["dispatch_ms_after_ready"] = (time.perf_counter() - ready_at) * 1000
        try:
            await ItemEventHandler._handle_event(handler, "del", 1)
        finally:
            done.set_result(None)

    heartbeat_delays: list[float] = []
    measuring = True

    def heartbeat(deadline: float) -> None:
        heartbeat_delays.append((time.perf_counter() - deadline) * 1000)
        if measuring:
            loop.call_later(0.005, heartbeat, time.perf_counter() + 0.005)

    # Refresh uvloop's cached clock before scheduling the ready+5ms callback.
    await asyncio.sleep(0.010)
    ready_at = time.perf_counter() + 0.005
    loop.call_later(0.005, heartbeat, ready_at)
    with patch.object(Message, "delete", delete):
        loop.call_later(
            0.005, lambda: callback_tasks.append(asyncio.create_task(callback()))
        )
        start = time.perf_counter()
        await operation()
        marks["operation_ms"] = (time.perf_counter() - start) * 1000
        await done
        await callback_tasks[0]
        measuring = False
        # Let the final heartbeat fire before another probe starts.
        await asyncio.sleep(0.010)
    marks["heartbeat_max_lateness_ms"] = max(heartbeat_delays)
    marks["heartbeat_samples"] = len(heartbeat_delays)
    return marks


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for label in dict.fromkeys(record["label"] for record in records):
        selected = [r for r in records if r["label"] == label]
        summary[label] = {"n": len(selected)}
        for metric in (
            "operation_ms",
            "dispatch_ms_after_ready",
            "delete_ms_after_ready",
            "heartbeat_max_lateness_ms",
        ):
            values = [r[metric] for r in selected]
            summary[label][metric] = {
                "median": statistics.median(values),
                "min": min(values),
                "max": max(values),
            }
    return summary


async def trial(args: argparse.Namespace) -> dict[str, Any]:
    selected = (
        baseline_service(args.baseline_revision)
        if args.mode == "before"
        else GalleryDlService
    )
    records: list[dict[str, Any]] = []
    loop_thread = threading.get_ident()
    constructor_threads: list[int] = []
    original_init = DataJob.__init__
    fixture = REPO / "bot/tests/fixtures/gallery_dl/tiktok-slideshow.json"
    html = (
        '<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">'
        + fixture.read_text()
        + "</script>"
    ).encode()
    attempts: list[str] = []
    cpu_control = False

    def request(extractor: Any, url: str) -> Response:
        if cpu_control:
            deadline = time.perf_counter() + 0.150
            while time.perf_counter() < deadline:
                pass
        response = Response()
        response.url = url
        response.status_code = 200
        response._content = html
        return response

    def construct(job: DataJob, *args: Any, **kwargs: Any) -> None:
        constructor_threads.append(threading.get_ident())
        original_init(job, *args, **kwargs)
        # Patch the HTTP boundary after real URL selection. This keeps lazy
        # extractor imports cold, including for the full fallback cold trial.
        job.extractor.request = MethodType(request, job.extractor)

    async def construct_only() -> None:
        assert await selected._extract_json_data(URL) == []

    def forbid_connect(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Offline probe attempted a network connection")

    async def fail(source: Any, url: str) -> None:
        attempts.append(type(source).__name__)
        raise SourceInfoExtractFailed(source)

    async def fallback() -> None:
        result = await TikTokInfoExtractor.get_video_info(URL)
        assert result.images_urls == [
            "https://example.invalid/first.jpg",
            "https://example.invalid/second.jpg",
        ]
        assert (result.width, result.height) == (720, 1080)
        assert result.music_url == "https://example.invalid/music.mp3"

    with (
        patch.object(socket.socket, "connect", forbid_connect),
        patch.object(socket.socket, "connect_ex", forbid_connect),
        patch.object(GkfeedApi, "delete_item_by_id", AsyncMock()),
        patch.object(DataJob, "__init__", construct),
        patch.object(type(_EXTRACTORS[0]), "get_video_info", fail),
        patch.object(type(_EXTRACTORS[1]), "get_video_info", fail),
        patch.object(fallback_module, "GalleryDlService", selected),
        patch.object(HttpService, "get_redirected_url", AsyncMock(return_value=URL)),
    ):
        records.append(await probe("idle", lambda: asyncio.sleep(0.025)))
        # Each cold scenario gets its own fresh Python process in a series.
        if args.cold_scenario == "construct":
            with patch.object(DataJob, "run", return_value=0):
                records.append(await probe("construct_cold", construct_only))
        else:
            records.append(await probe("real_run_fallback_cold", fallback))

        with patch.object(DataJob, "run", return_value=0):
            for _ in range(args.repetitions):
                records.append(await probe("construct_warm", construct_only))

        for _ in range(args.repetitions):
            records.append(await probe("real_run_fallback_warm", fallback))

        # Explicit synthetic control for GIL contention during a running job.
        # This is not a measured TikTok workload or a production percentile.
        cpu_control = True
        records.append(await probe("synthetic_gil_150ms_fallback", fallback))

        expected_attempts = [type(source).__name__ for source in _EXTRACTORS[:2]]
        fallback_count = args.repetitions + 1 + (args.cold_scenario == "fallback")
        assert attempts == expected_attempts * fallback_count

    return {
        "mode": args.mode,
        "cold_scenario": args.cold_scenario,
        "baseline_revision": args.baseline_revision,
        "python": sys.version,
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("gallery-dl", "aiogram", "uvloop")
        },
        "switch_interval_ms": sys.getswitchinterval() * 1000,
        "constructor_on_loop": [
            thread == loop_thread for thread in constructor_threads
        ],
        "extractor_order": [type(source).__name__ for source in _EXTRACTORS],
        "fallback_attempts": attempts,
        "records": records,
        "summary": summarize(records),
    }


def series(args: argparse.Namespace) -> dict[str, Any]:
    trials: list[dict[str, Any]] = []
    for index in range(args.processes):
        # Alternate order to reduce before/after bias from filesystem caches.
        modes = ("before", "after") if index % 2 == 0 else ("after", "before")
        for scenario in ("construct", "fallback"):
            for mode in modes:
                output = args.output.with_name(
                    f"{args.output.stem}-{index:02}-{scenario}-{mode}.json"
                )
                subprocess.run(
                    [
                        sys.executable,
                        __file__,
                        "--mode",
                        mode,
                        "--cold-scenario",
                        scenario,
                        "--repetitions",
                        str(args.repetitions),
                        "--baseline-revision",
                        args.baseline_revision,
                        "--output",
                        str(output),
                    ],
                    cwd=REPO,
                    check=True,
                    stdout=subprocess.DEVNULL,
                )
                trials.append(json.loads(output.read_text()))
    records = [
        {**record, "label": f"{trial['mode']}_{record['label']}"}
        for trial in trials
        for record in trial["records"]
    ]
    return {"trials": trials, "summary": summarize(records)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-revision", default=BASELINE)
    parser.add_argument("--mode", choices=("before", "after"), default="before")
    parser.add_argument(
        "--cold-scenario", choices=("construct", "fallback"), default="construct"
    )
    parser.add_argument("--processes", type=int, default=0)
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = series(args) if args.processes else uvloop.run(trial(args))
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["summary"], indent=2))
