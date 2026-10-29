import asyncio
import threading
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import AsyncMock, patch

import pytest

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
    monkeypatch.setattr(FfmpegService, "download_and_prepare_audio", audio)
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


async def test_voice_conversion_still_returns_bytes(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def run(command: list[str]) -> None:
        assert Path(command[command.index("-i") + 1]).read_bytes() == b"music"
        assert "libopus" in command
        Path(command[-1]).write_bytes(b"voice")

    monkeypatch.setattr(FfmpegService, "_run_command", run)
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

    monkeypatch.setattr(FfmpegService, "_run_command", run)
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

    monkeypatch.setattr(FfmpegService, "_run_command", run)
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


async def test_small_video_does_not_get_reencoded(tmp_path: Path) -> None:
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"small video")

    with patch.object(
        FfmpegService, "_compress_video_to_size", new_callable=AsyncMock
    ) as compress_video:
        result = await FfmpegService.compress_video_if_needed(
            str(video_path), max_size_bytes=15 * 1024 * 1024, max_width=720
        )

    assert result == str(video_path)
    compress_video.assert_not_awaited()


async def test_large_video_uses_size_limited_encoding(tmp_path: Path) -> None:
    video_path = tmp_path / "video.mp4"

    with (
        patch("services.ffmpeg.os.path.getsize", return_value=20 * 1024 * 1024),
        patch.object(
            FfmpegService, "_compress_video_to_size", new_callable=AsyncMock
        ) as compress_video,
    ):
        result = await FfmpegService.compress_video_if_needed(
            str(video_path), max_size_bytes=15 * 1024 * 1024, max_width=720
        )

    compressed_path = tmp_path / "video_compressed.mp4"
    assert result == str(compressed_path)
    compress_video.assert_awaited_once_with(
        str(video_path), str(compressed_path), 15 * 1024 * 1024, 720
    )


async def test_size_limited_encoding_calculates_two_pass_bitrate() -> None:
    with (
        patch.object(
            FfmpegService,
            "get_video_metadata",
            new_callable=AsyncMock,
            return_value={"duration": 60},
        ),
        patch.object(
            FfmpegService, "_run_command", new_callable=AsyncMock
        ) as run_command,
    ):
        await FfmpegService._compress_video_to_size(
            "input.mp4", "output.mp4", max_size_bytes=15 * 1024 * 1024, max_width=720
        )

    first_pass, second_pass = [call.args[0] for call in run_command.await_args_list]
    assert first_pass[first_pass.index("-pass") + 1] == "1"
    assert "-an" in first_pass
    assert second_pass[second_pass.index("-pass") + 1] == "2"
    assert second_pass[second_pass.index("-b:v") + 1] == "1843322"
    assert second_pass[second_pass.index("-b:a") + 1] == "128000"
