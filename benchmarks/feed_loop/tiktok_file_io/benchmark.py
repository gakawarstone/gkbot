"""Compare production TikTok file paths without network, DB, ffmpeg or uploads.

Run under the shared measurement flock. The input MP4 is only read; temporary
files are created and removed under this script's directory on the same disk.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
import pickle
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import types
from collections.abc import Awaitable, Callable
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import uvloop

# Do not read deployment secrets via extractor/downloader imports.
environment = types.ModuleType("configs.env")
environment.BROKER_URL = None
sys.modules["configs.env"] = environment

from services.cache_dir import CacheDir
from services.ffmpeg import FfmpegService
from services.http import HttpService
from services.schedule import Schedule, Task
from services.tiktok import TikTokService, _TikTokCacheDir
from services.tiktok.extractor import TikTokInfoExtractor
from services.tiktok.types import InfoVideoTikTok

BASELINE = "28a0081f7b25ea2c33192b5596d1e22356f1fdd9"
Operation = Callable[[], Awaitable[Any]]


async def noop(*args: Any, **kwargs: Any) -> None:
    pass


def baseline_class(path: str, name: str, package: str) -> tuple[type, dict[str, Any]]:
    source = subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], text=True)
    namespace: dict[str, Any] = {"__package__": package, "__name__": package}
    # Execute only the pinned, locally checked-out baseline for this comparison.
    exec(compile(source, f"{BASELINE}:{path}", "exec"), namespace)  # noqa: S102
    return namespace[name], namespace


async def measure(operation: Operation) -> dict[str, float | int]:
    ready = asyncio.Event()
    samples: list[tuple[float, float]] = []
    ended = float("inf")

    async def heartbeat() -> None:
        while True:
            deadline = time.perf_counter() + 0.001
            ready.set()
            await asyncio.sleep(0.001)
            now = time.perf_counter()
            samples.append((now, max(0.0, now - deadline)))
            if now >= ended:
                return

    timer = asyncio.create_task(heartbeat())
    await ready.wait()
    start = time.perf_counter()
    value = await operation()
    ended = time.perf_counter()
    await timer
    del value
    return {
        "wall_ms": (ended - start) * 1000,
        "max_lag_ms": max(lag for _, lag in samples) * 1000,
        "samples": len(samples),
        "post_samples": sum(now >= ended for now, _ in samples),
    }


def summary(runs: list[dict[str, float | int]]) -> dict[str, dict[str, float]]:
    result = {}
    for key in ("wall_ms", "max_lag_ms"):
        values = sorted(float(run[key]) for run in runs)
        result[key] = {
            "median": statistics.median(values),
            "p95": values[math.ceil(len(values) * 0.95) - 1],
        }
    return result


async def main(source: Path, output: Path, repetitions: int) -> None:
    measured_at = datetime.now(UTC).isoformat()
    old_ffmpeg, _ = baseline_class(
        "bot/services/ffmpeg.py", "FfmpegService", "services"
    )
    old_tiktok, namespace = baseline_class(
        "bot/services/tiktok/__init__.py", "TikTokService", "services.tiktok"
    )
    namespace["FfmpegService"] = old_ffmpeg
    payload = source.read_bytes()
    script_dir = Path(__file__).resolve().parent
    assert source.stat().st_dev == script_dir.stat().st_dev
    cases: dict[str, Any] = {}
    await asyncio.to_thread(lambda: None)

    async def idle() -> None:
        await asyncio.sleep(0.025)

    async def baseline(name: str) -> None:
        runs = [await measure(idle) for _ in range(repetitions)]
        cases[name] = {"summary": summary(runs), "runs": runs}

    await baseline("idle_before")
    with tempfile.TemporaryDirectory(prefix=".scratch-", dir=script_dir) as scratch:
        root = Path(scratch)
        for scenario in ("video", "slideshow", "cleanup"):
            for variant in ("current", "fixed"):
                runs = []
                for index in range(repetitions + 1):
                    with (
                        tempfile.TemporaryDirectory(dir=root) as case_root,
                        ExitStack() as stack,
                    ):
                        stack.enter_context(
                            patch.object(CacheDir, "_CacheDir__base_path", case_root)
                        )
                        tasks: list[Task] = []

                        async def schedule(
                            task: Task, delay_seconds: int, tasks: list[Task] = tasks
                        ) -> None:
                            assert delay_seconds == 300
                            tasks.append(pickle.loads(pickle.dumps(task)))

                        async def get_payload(*args: Any, **kwargs: Any) -> bytes:
                            return payload

                        stack.enter_context(
                            patch.object(Schedule, "run_task_after", schedule)
                        )
                        stack.enter_context(
                            patch.object(HttpService, "get", get_payload)
                        )
                        service = TikTokService if variant == "fixed" else old_tiktok
                        ffmpeg = FfmpegService if variant == "fixed" else old_ffmpeg
                        info = InfoVideoTikTok(
                            "https://benchmark.invalid/video",
                            None,
                            None,
                            None,
                            1080,
                            720,
                            9,
                        )
                        if scenario == "slideshow":
                            info.video_url = None
                            info.images_urls = ["https://benchmark.invalid/image"]
                            cache = (
                                _TikTokCacheDir() if variant == "fixed" else CacheDir()
                            )
                            filename = (
                                "video.mp4" if variant == "fixed" else "slideshow.mp4"
                            )
                            shutil.copyfile(source, cache.get_file_path(filename))
                            stack.enter_context(
                                patch.object(
                                    ffmpeg, "download_and_prepare_images", noop
                                )
                            )
                            stack.enter_context(
                                patch.object(ffmpeg, "_run_command", noop)
                            )
                            if variant == "fixed":

                                def adopt_output(
                                    target: CacheDir, cache: CacheDir = cache
                                ) -> None:
                                    target.path = cache.path

                                stack.enter_context(
                                    patch.object(CacheDir, "__init__", adopt_output)
                                )
                            else:
                                stack.enter_context(
                                    patch.dict(
                                        old_ffmpeg.make_slideshow_from_web.__func__.__globals__,
                                        {"CacheDir": lambda cache=cache: cache},
                                    )
                                )

                        async def extract(
                            *args: Any, info: InfoVideoTikTok = info, **kwargs: Any
                        ) -> InfoVideoTikTok:
                            return info

                        stack.enter_context(
                            patch.object(TikTokInfoExtractor, "get_video_info", extract)
                        )

                        async def get_video(service: type = service) -> Any:
                            return await service.get_video(
                                "https://benchmark.invalid/tiktok"
                            )

                        operation = get_video
                        if scenario == "cleanup":
                            await get_video()
                            assert len(tasks) == 1
                            operation = tasks[0].run
                        run = await measure(operation)
                        if scenario != "cleanup":
                            assert len(tasks) == 1
                            # The return path remains usable after the service returns.
                            assert info.video_input_file is not None
                            assert Path(
                                info.video_input_file.path
                            ).stat().st_size == len(payload)
                        if index:
                            runs.append(run)
                        await asyncio.sleep(0.003)
                name = f"{scenario}_{variant}"
                cases[name] = {"summary": summary(runs), "runs": runs}
                print(json.dumps({"case": name, **summary(runs)}), flush=True)
    await baseline("idle_after")
    result = {
        "baseline": BASELINE,
        "measured_at": measured_at,
        "python": platform.python_version(),
        "uvloop": uvloop.__version__,
        "platform": platform.platform(),
        "input": {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()},
        "filesystem": (
            await asyncio.to_thread(
                subprocess.check_output, ["df", "-T", str(script_dir)], text=True
            )
        ).strip(),
        "load_average": os.getloadavg(),
        "repetitions": repetitions,
        "cases": cases,
    }
    assert all(
        run["post_samples"] >= 1 for case in cases.values() for run in case["runs"]
    )
    output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repetitions", type=int, default=20)
    args = parser.parse_args()
    if args.repetitions < 20:
        parser.error("Use at least 20 repetitions")
    uvloop.run(main(args.input, args.output, args.repetitions))
