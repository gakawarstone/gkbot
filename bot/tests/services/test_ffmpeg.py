import asyncio
import threading
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import AsyncMock

import pytest

from services.audio import AudioService
from services.cache_dir import CacheDir
from services.ffmpeg import FfmpegService


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
    monkeypatch.setattr(AudioService, "download_and_prepare_audio", audio)
    monkeypatch.setattr(FfmpegService, "_run_command", run)
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


@pytest.mark.parametrize("audio_input", [None, "audio.m4a"])
def test_slideshow_command_preserves_input_option_order(
    audio_input: str | None,
) -> None:
    audio_options = ["-stream_loop", "-1", "-i", audio_input] if audio_input else []
    assert FfmpegService._build_slideshow_command("*.jpg", audio_input, "out.mp4") == [
        "ffmpeg",
        "-y",
        "-framerate",
        "1/3",
        "-pattern_type",
        "glob",
        "-i",
        "*.jpg",
        *audio_options,
        "-c:v",
        "libx264",
        *(["-shortest"] if audio_input else []),
        "-vf",
        "scale=720:1080",
        "-r",
        "30",
        "-pix_fmt",
        "yuv420p",
        "out.mp4",
    ]


async def test_cancelled_slideshow_finishes_before_cleanup(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch
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

    monkeypatch.setattr(FfmpegService, "_run_command", run)
    monkeypatch.setattr(FfmpegService, "download_and_prepare_images", AsyncMock())
    task = asyncio.create_task(FfmpegService.make_slideshow_from_web(["image"], None))
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
