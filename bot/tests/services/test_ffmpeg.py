import asyncio
import json
import threading
from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess
from unittest.mock import AsyncMock

import pytest

from services.cache_dir import CacheDir
from services.ffmpeg import FfmpegService
from services.ffmpeg_runner import FfmpegRunner


@pytest.fixture
async def cache_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(CacheDir, "_CacheDir__base_path", str(tmp_path))
    return tmp_path


@pytest.mark.parametrize("audio_url", [None, "https://example.invalid/audio"])
async def test_slideshow_file_uses_owned_output_directory(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch, audio_url: str | None
) -> None:
    images = AsyncMock()
    audio = AsyncMock()
    run = AsyncMock()
    monkeypatch.setattr(FfmpegService, "download_and_prepare_images", images)
    monkeypatch.setattr(FfmpegService, "download_and_prepare_audio", audio)
    monkeypatch.setattr(FfmpegRunner, "run", run)
    output_path = str(cache_root / "video.mp4")
    urls = ["https://example.invalid/image"]
    await FfmpegService.make_slideshow_file_from_web(urls, audio_url, output_path)
    images.assert_awaited_once_with(urls, str(cache_root))
    assert run.await_args is not None
    command = run.await_args.args[0]
    assert command[-1] == output_path
    assert str(cache_root / "*.jpg") in command
    if audio_url:
        audio.assert_awaited_once_with(audio_url, str(cache_root))
        assert str(cache_root / "audio.m4a") in command
        assert "-shortest" in command
    else:
        audio.assert_not_awaited()
        assert "-shortest" not in command


@pytest.mark.parametrize("fail", [False, True])
async def test_slideshow_bytes_compatibility_and_cleanup(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch, fail: bool
) -> None:
    async def generate(urls: list[str], audio: str | None, output: str) -> None:
        Path(output).write_bytes(b"slideshow")
        if fail:
            raise CalledProcessError(1, "ffmpeg")

    monkeypatch.setattr(FfmpegService, "make_slideshow_file_from_web", generate)
    if fail:
        with pytest.raises(CalledProcessError):
            await FfmpegService.make_slideshow_from_web(["image"], None)
    else:
        assert (
            await FfmpegService.make_slideshow_from_web(["image"], None) == b"slideshow"
        )
    assert list(cache_root.iterdir()) == []


@pytest.mark.parametrize(
    ("probe_output", "expected"),
    [
        ({"streams": []}, {}),
        ({}, {}),
        (
            {"streams": [{"width": 720, "height": "1080", "duration": "12.9"}]},
            {"width": 720, "height": 1080, "duration": 12},
        ),
        ({"streams": [{"width": 720, "duration": "N/A"}]}, {"width": 720}),
    ],
)
async def test_metadata_parses_probe_output(
    monkeypatch: pytest.MonkeyPatch,
    probe_output: dict,
    expected: dict[str, int],
) -> None:
    run = AsyncMock(
        return_value=CompletedProcess([], 0, stdout=json.dumps(probe_output))
    )
    monkeypatch.setattr(FfmpegRunner, "run", run)
    assert await FfmpegService.get_video_metadata("input file.mp4") == expected


async def test_voice_conversion_still_returns_bytes(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def run(command: list[str]) -> None:
        assert Path(command[command.index("-i") + 1]).read_bytes() == b"music"
        assert "libopus" in command
        Path(command[-1]).write_bytes(b"voice")

    monkeypatch.setattr(FfmpegRunner, "run", run)
    assert await FfmpegService.convert_music_to_voice(b"music") == b"voice"
    assert list(cache_root.iterdir()) == []


@pytest.mark.parametrize("failure", ["save", "command", "read", "removed"])
async def test_voice_conversion_cleans_up_on_failure(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    error = CalledProcessError(1, "ffmpeg")

    async def run(command: list[str]) -> None:
        if failure == "removed":
            Path(command[command.index("-i") + 1]).unlink()
            Path(command[-1]).parent.rmdir()
        if failure in ("command", "removed"):
            raise error
        # No output file: reading the converted audio must fail.

    def fail_save(cache: CacheDir, name: str, content: bytes) -> None:
        Path(cache.get_file_path(name)).write_bytes(content[:1])
        raise OSError("write failed")

    monkeypatch.setattr(FfmpegRunner, "run", run)
    if failure == "save":
        monkeypatch.setattr(CacheDir, "save_file", fail_save)
    expected_error = (
        CalledProcessError if failure in ("command", "removed") else OSError
    )
    with pytest.raises(expected_error) as raised:
        await FfmpegService.convert_music_to_voice(b"music")
    if failure in ("command", "removed"):
        assert raised.value is error
    assert list(cache_root.iterdir()) == []


@pytest.mark.parametrize("conversion", ["voice", "slideshow"])
async def test_cancelled_conversion_finishes_before_cleanup(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch, conversion: str
) -> None:
    started = threading.Event()
    release = threading.Event()

    def write(output_path: str) -> None:
        started.set()
        assert release.wait(timeout=5)
        assert Path(output_path).parent.is_dir()
        Path(output_path).write_bytes(b"converted")

    async def run(command: list[str]) -> None:
        await asyncio.to_thread(write, command[-1])

    monkeypatch.setattr(FfmpegRunner, "run", run)
    monkeypatch.setattr(FfmpegService, "download_and_prepare_images", AsyncMock())
    operation = (
        FfmpegService.convert_music_to_voice(b"music")
        if conversion == "voice"
        else FfmpegService.make_slideshow_from_web(["image"], None)
    )
    task = asyncio.create_task(operation)
    try:
        assert await asyncio.to_thread(started.wait, 5)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        assert len(list(cache_root.iterdir())) == 1
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert list(cache_root.iterdir()) == []


@pytest.mark.parametrize("remove_directory", [False, True])
async def test_slideshow_bytes_cleanup_when_output_is_missing(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch, remove_directory: bool
) -> None:
    async def generate(urls: list[str], audio: str | None, output: str) -> None:
        if remove_directory:
            Path(output).parent.rmdir()

    monkeypatch.setattr(FfmpegService, "make_slideshow_file_from_web", generate)
    with pytest.raises(FileNotFoundError):
        await FfmpegService.make_slideshow_from_web(["image"], None)
    assert list(cache_root.iterdir()) == []
