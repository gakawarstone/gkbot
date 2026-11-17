import asyncio
import threading
from pathlib import Path
from subprocess import CalledProcessError

import pytest

from services.audio import AudioService
from services.cache_dir import CacheDir
from services.ffmpeg_runner import FfmpegRunner


@pytest.fixture
async def cache_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(CacheDir, "_CacheDir__base_path", str(tmp_path))
    return tmp_path


async def test_voice_conversion_still_returns_bytes(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def run(command: list[str]) -> None:
        assert Path(command[command.index("-i") + 1]).read_bytes() == b"music"
        assert "libopus" in command
        Path(command[-1]).write_bytes(b"voice")

    monkeypatch.setattr(FfmpegRunner, "run", run)
    assert await AudioService.convert_music_to_voice(b"music") == b"voice"
    assert list(cache_root.iterdir()) == []


async def test_audio_preparation_writes_to_caller_owned_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    url = "https://example.invalid/audio?token=a b"

    async def run(command: list[str]) -> None:

        Path(command[-1]).write_bytes(b"audio")

    monkeypatch.setattr(FfmpegRunner, "run", run)
    await AudioService.download_and_prepare_audio(url, str(tmp_path))
    assert (tmp_path / "audio.m4a").read_bytes() == b"audio"


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
        await AudioService.convert_music_to_voice(b"music")
    if failure in ("command", "removed"):
        assert raised.value is error
    assert list(cache_root.iterdir()) == []


async def test_cancelled_voice_finishes_before_cleanup(
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

    monkeypatch.setattr(FfmpegRunner, "run", run)
    task = asyncio.create_task(AudioService.convert_music_to_voice(b"music"))
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
