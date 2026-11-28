import asyncio
import pickle
import threading
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot

from services.audio import AudioService
from services.cache_dir import CacheDir
from services.ffmpeg_runner import FfmpegRunner
from services.http import HttpService
from services.schedule import Schedule, Task
from services.slideshow import SlideshowRenderer
from services.tiktok import TikTokService, _TikTokCacheDir
from services.tiktok.exceptions import TikTokInfoExtractionFailed
from services.tiktok.extractor import TikTokInfoExtractor
from services.tiktok.types import InfoVideoTikTok
from services.video_metadata import VideoMetadataService
from ui.media import media_input_file


@pytest.fixture
async def cache_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(CacheDir, "_CacheDir__base_path", str(tmp_path))
    return tmp_path


@pytest.fixture
async def scheduled(monkeypatch: pytest.MonkeyPatch) -> list[Task]:
    tasks: list[Task] = []

    async def schedule(task: Task, delay_seconds: int) -> None:
        assert delay_seconds == 300
        tasks.append(pickle.loads(pickle.dumps(task)))

    monkeypatch.setattr(Schedule, "run_task_after", schedule)
    return tasks


async def get_video(info: InfoVideoTikTok, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(
        TikTokInfoExtractor, "get_video_info", AsyncMock(return_value=info)
    )
    monkeypatch.setattr(
        VideoMetadataService,
        "get_video_metadata",
        AsyncMock(return_value={"height": 1080, "width": 720, "duration": 9}),
    )
    video = await TikTokService.get_video("https://example.invalid/tiktok")
    assert isinstance(video.file, Path)
    assert (video.height, video.width, video.duration) == (1080, 720, 9)
    return video.file


async def test_download_writes_off_loop_and_survives_return(
    cache_root: Path, scheduled: list[Task], monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = b"video contents"
    loop_thread = threading.get_ident()
    save_file = CacheDir.save_file

    def save(cache: CacheDir, name: str, content: bytes) -> None:
        assert threading.get_ident() != loop_thread
        save_file(cache, name, content)

    monkeypatch.setattr(CacheDir, "save_file", save)
    monkeypatch.setattr(HttpService, "get", AsyncMock(return_value=payload))
    info = InfoVideoTikTok("https://example.invalid/video", None, None, None)
    path = await get_video(info, monkeypatch)
    assert path.read_bytes() == payload
    assert len(scheduled) == 1

    delete = CacheDir.delete

    def delete_off_loop(cache: CacheDir) -> None:
        assert threading.get_ident() != loop_thread
        delete(cache)

    monkeypatch.setattr(CacheDir, "delete", delete_off_loop)
    await scheduled[0].run()
    assert list(cache_root.iterdir()) == []


@pytest.mark.parametrize("audio_url", [None, "https://example.invalid/music"])
async def test_slideshow_output_remains_available_until_scheduled_cleanup(
    cache_root: Path,
    scheduled: list[Task],
    monkeypatch: pytest.MonkeyPatch,
    audio_url: str | None,
) -> None:
    async def run(command: list[str]) -> None:
        Path(command[-1]).write_bytes(b"generated slideshow")

    monkeypatch.setattr(SlideshowRenderer, "download_and_prepare_images", AsyncMock())
    monkeypatch.setattr(AudioService, "download_and_prepare_audio", AsyncMock())
    monkeypatch.setattr(FfmpegRunner, "run", run)
    info = InfoVideoTikTok(None, None, audio_url, ["https://example.invalid/image"])
    path = await get_video(info, monkeypatch)
    assert path.read_bytes() == b"generated slideshow"
    assert len(list(cache_root.iterdir())) == 1
    await scheduled[0].run()
    assert list(cache_root.iterdir()) == []


@pytest.mark.parametrize(
    "failure", ["download", "save", "ffmpeg", "schedule", "invalid"]
)
async def test_failed_preparation_cleans_directory(
    cache_root: Path,
    scheduled: list[Task],
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    monkeypatch.setattr(HttpService, "get", AsyncMock(return_value=b"video"))
    info = InfoVideoTikTok("https://example.invalid/video", None, None, None)
    error: Exception = OSError("test failure")
    if failure == "download":
        monkeypatch.setattr(HttpService, "get", AsyncMock(side_effect=error))
    elif failure == "save":

        def fail_save(cache: CacheDir, name: str, content: bytes) -> None:
            Path(cache.get_file_path(name)).write_bytes(content[:1])
            raise error

        monkeypatch.setattr(CacheDir, "save_file", fail_save)
    elif failure == "ffmpeg":
        info = InfoVideoTikTok(None, None, None, ["https://example.invalid/image"])
        error = CalledProcessError(1, "ffmpeg")
        monkeypatch.setattr(
            SlideshowRenderer,
            "download_and_prepare_images",
            AsyncMock(side_effect=error),
        )
    elif failure == "schedule":
        monkeypatch.setattr(Schedule, "run_task_after", AsyncMock(side_effect=error))
    else:
        info = InfoVideoTikTok(None, None, None, None)
        error = TikTokInfoExtractionFailed("")
    monkeypatch.setattr(
        TikTokInfoExtractor, "get_video_info", AsyncMock(return_value=info)
    )
    with pytest.raises(type(error)):
        await TikTokService.get_video("https://example.invalid/tiktok")
    assert list(cache_root.iterdir()) == []
    assert scheduled == []


async def test_cancelled_write_finishes_before_cleanup(
    cache_root: Path, scheduled: list[Task], monkeypatch: pytest.MonkeyPatch
) -> None:
    started = threading.Event()
    release = threading.Event()
    save_file = CacheDir.save_file

    def save(cache: CacheDir, name: str, content: bytes) -> None:
        started.set()
        assert release.wait(timeout=5)
        assert Path(cache.path).exists()
        save_file(cache, name, content)

    monkeypatch.setattr(CacheDir, "save_file", save)
    monkeypatch.setattr(HttpService, "get", AsyncMock(return_value=b"video"))
    monkeypatch.setattr(
        TikTokInfoExtractor,
        "get_video_info",
        AsyncMock(
            return_value=InfoVideoTikTok(
                "https://example.invalid/video", None, None, None
            )
        ),
    )
    task = asyncio.create_task(
        TikTokService.get_video("https://example.invalid/tiktok")
    )
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
    assert scheduled == []


@pytest.mark.parametrize("slideshow", [False, True])
async def test_scheduled_cleanup_defers_during_upload(
    cache_root: Path,
    scheduled: list[Task],
    monkeypatch: pytest.MonkeyPatch,
    slideshow: bool,
) -> None:
    payload = b"v" * 100_000
    monkeypatch.setattr(HttpService, "get", AsyncMock(return_value=payload))
    info = InfoVideoTikTok("https://example.invalid/video", None, None, None)
    if slideshow:

        async def render(urls: list[str], audio: str | None, output: str) -> None:
            Path(output).write_bytes(payload)

        monkeypatch.setattr(SlideshowRenderer, "make_slideshow_file_from_web", render)
        info = InfoVideoTikTok(None, None, None, ["image"])
    path = await get_video(info, monkeypatch)
    reader = media_input_file(path, protect_from_cleanup=True).read(
        Bot("12345678:token")
    )
    assert await anext(reader)
    await scheduled[0].run()
    assert path.exists()
    assert len(scheduled) == 2
    await reader.aclose()
    assert not _TikTokCacheDir._active_readers
    await scheduled[1].run()
    assert list(cache_root.iterdir()) == []


async def test_existing_file_and_metadata_are_preserved(
    cache_root: Path, scheduled: list[Task], monkeypatch: pytest.MonkeyPatch
) -> None:
    path = cache_root / "existing.mp4"
    info = InfoVideoTikTok(None, path, None, None, 480, 640, 12)
    monkeypatch.setattr(
        TikTokInfoExtractor, "get_video_info", AsyncMock(return_value=info)
    )
    metadata = AsyncMock()
    monkeypatch.setattr(VideoMetadataService, "get_video_metadata", metadata)
    video = await TikTokService.get_video("https://example.invalid/tiktok")
    assert video.file == path
    assert (video.height, video.width, video.duration) == (480, 640, 12)
    metadata.assert_not_awaited()
    assert scheduled == []


async def test_cancelled_slideshow_finishes_before_cleanup(
    cache_root: Path, scheduled: list[Task], monkeypatch: pytest.MonkeyPatch
) -> None:
    started = asyncio.Event()
    release = asyncio.Event()

    async def run(command: list[str]) -> None:
        started.set()
        await release.wait()
        Path(command[-1]).write_bytes(b"slideshow")

    monkeypatch.setattr(SlideshowRenderer, "download_and_prepare_images", AsyncMock())
    monkeypatch.setattr(FfmpegRunner, "run", run)
    monkeypatch.setattr(
        TikTokInfoExtractor,
        "get_video_info",
        AsyncMock(return_value=InfoVideoTikTok(None, None, None, ["image"])),
    )
    task = asyncio.create_task(
        TikTokService.get_video("https://example.invalid/tiktok")
    )
    await started.wait()
    try:
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        assert len(list(cache_root.iterdir())) == 1
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert list(cache_root.iterdir()) == []
    assert scheduled == []


async def test_metadata_probe_failure_keeps_uploadable_file(
    cache_root: Path, scheduled: list[Task], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(HttpService, "get", AsyncMock(return_value=b"video"))
    monkeypatch.setattr(
        TikTokInfoExtractor,
        "get_video_info",
        AsyncMock(return_value=InfoVideoTikTok(None, None, None, ["image"])),
    )

    async def run(command: list[str]) -> None:
        Path(command[-1]).write_bytes(b"slideshow")

    monkeypatch.setattr(SlideshowRenderer, "download_and_prepare_images", AsyncMock())
    monkeypatch.setattr(FfmpegRunner, "run", run)
    monkeypatch.setattr(
        VideoMetadataService,
        "get_video_metadata",
        AsyncMock(side_effect=CalledProcessError(1, "ffprobe")),
    )
    video = await TikTokService.get_video("https://example.invalid/tiktok")
    assert (video.height, video.width, video.duration) == (1080, 720, None)
    assert isinstance(video.file, Path)
    assert video.file.read_bytes() == b"slideshow"
    await scheduled[0].run()
    assert list(cache_root.iterdir()) == []
