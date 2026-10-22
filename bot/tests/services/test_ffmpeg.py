from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import AsyncMock

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
