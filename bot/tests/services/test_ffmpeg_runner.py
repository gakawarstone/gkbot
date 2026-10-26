import asyncio
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

from services.ffmpeg_runner import FfmpegRunner
from services.video_conversion import VideoConversionService


@pytest.fixture(autouse=True)
def fresh_process_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(FfmpegRunner, "_semaphore", asyncio.Semaphore(1))


async def test_run_executes_outside_the_event_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = ["ffprobe", "input.mp4"]
    result = subprocess.CompletedProcess(command, 0, stdout="result", stderr="")
    event_loop_thread = threading.get_ident()

    def run(arguments: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
        assert threading.get_ident() != event_loop_thread
        return result

    monkeypatch.setattr(subprocess, "run", run)
    assert await FfmpegRunner.run(command, capture_output=True, text=True) is result


async def test_ffmpeg_and_ffprobe_share_the_service_process_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = asyncio.Event()
    release = asyncio.Event()

    async def execute(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
        if command[0] == "ffmpeg":
            started.set()
            await release.wait()
        return subprocess.CompletedProcess(command, 0)

    executor = AsyncMock(side_effect=execute)
    monkeypatch.setattr("services.ffmpeg_runner.async_wrap", lambda function: executor)
    first = asyncio.create_task(
        VideoConversionService.convert_video("input.mp4", "output.mp4")
    )
    await asyncio.wait_for(started.wait(), timeout=5)
    second = asyncio.create_task(FfmpegRunner.run(["ffprobe"]))
    try:
        await asyncio.sleep(0)
        assert executor.await_count == 1
        assert not second.done()
    finally:
        release.set()
        results = await asyncio.wait_for(asyncio.gather(first, second), timeout=5)
    assert results[0] is None
    assert results[1].args == ["ffprobe"]
    assert executor.await_count == 2


async def test_process_failure_propagates_and_releases_limit() -> None:
    command = [
        sys.executable,
        "-c",
        "import sys; print('output'); print('failure', file=sys.stderr); sys.exit(7)",
    ]
    with pytest.raises(subprocess.CalledProcessError) as raised:
        await FfmpegRunner.run(command, capture_output=True, text=True)
    assert raised.value.returncode == 7
    assert raised.value.cmd == command
    assert raised.value.stdout == "output\n"
    assert raised.value.stderr == "failure\n"

    result = await asyncio.wait_for(
        FfmpegRunner.run(
            [sys.executable, "-c", "import sys; print(repr(sys.stdin.read()))"],
            capture_output=True,
            text=True,
        ),
        timeout=5,
    )
    assert result.stdout == "''\n"


async def test_missing_executable_propagates_and_releases_limit(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        await FfmpegRunner.run([str(tmp_path / "missing-ffmpeg")])
    result = await asyncio.wait_for(
        FfmpegRunner.run([sys.executable, "-c", "pass"]), timeout=5
    )
    assert result.returncode == 0


async def test_cancelled_waiter_does_not_start_a_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = AsyncMock()
    monkeypatch.setattr("services.ffmpeg_runner.async_wrap", lambda function: executor)
    async with FfmpegRunner._semaphore:
        waiting = asyncio.create_task(FfmpegRunner.run(["ffprobe"]))
        await asyncio.sleep(0)
        waiting.cancel()
        with pytest.raises(asyncio.CancelledError):
            await waiting
    executor.assert_not_awaited()
    await asyncio.wait_for(FfmpegRunner.run(["ffmpeg"]), timeout=5)
    executor.assert_awaited_once()
