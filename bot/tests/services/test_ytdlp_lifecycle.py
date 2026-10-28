import asyncio
import threading
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Self, cast
from unittest.mock import AsyncMock

import pytest
import yt_dlp
from aiogram.types import CallbackQuery, Chat, Message, User
from yt_dlp.utils import DownloadError

from modules.feed.handlers.callbacks import ItemEventHandler
from services.cache_dir import CacheDir
from services.ffmpeg import FfmpegService
from services.gkfeed import GkfeedCredentials
from services.gkfeed.api import GkfeedApi
from services.schedule import Schedule
from services.ytdlp import YtdlpDownloader
from services.ytdlp.source import DownloadSource

URL = "https://www.tiktok.com/@offline/video/1"
METADATA = {"title": "offline", "duration": 3, "height": 1080, "width": 720}


@pytest.mark.parametrize("operation", ["info", "download"])
async def test_delete_runs_while_ytdlp_lifecycle_is_busy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    loop_thread = threading.get_ident()
    started = threading.Event()
    release = threading.Event()
    threads: list[int] = []

    def stage(name: str) -> None:
        threads.append(threading.get_ident())
        assert threads[-1] != loop_thread
        if name == "operation":
            started.set()
            assert release.wait(5)

    class Downloader:
        def __init__(self, *args: Any) -> None:
            stage("construct")

        def __enter__(self) -> Self:
            stage("enter")
            return self

        def __exit__(self, *args: object) -> None:
            stage("exit")

        def extract_info(self, url: str, *, download: bool) -> dict[str, Any]:
            assert url == URL and not download
            stage("operation")
            return METADATA

        def download(self, url: str) -> None:
            assert url == URL
            stage("operation")

    monkeypatch.setattr(yt_dlp, "YoutubeDL", Downloader)
    monkeypatch.setattr(FfmpegService, "convert_video", AsyncMock())
    deleted = asyncio.Event()

    async def delete_message(message: Message, **kwargs: Any) -> bool:
        deleted.set()
        return True

    monkeypatch.setattr(Message, "delete", delete_message)
    monkeypatch.setattr(GkfeedApi, "delete_item_by_id", AsyncMock())
    query = CallbackQuery(
        id="offline",
        from_user=User(id=1, is_bot=False, first_name="offline"),
        chat_instance="offline",
        message=Message(
            message_id=1, date=datetime.now(UTC), chat=Chat(id=1, type="private")
        ),
    )
    task = asyncio.create_task(
        YtdlpDownloader._get_info(URL, DownloadSource.TIKTOK)
        if operation == "info"
        else YtdlpDownloader._download_file(
            URL, {"outtmpl": str(tmp_path / "video.mp4")}, DownloadSource.TIKTOK
        )
    )
    try:
        assert await asyncio.to_thread(started.wait, 5)
        credentials = AsyncMock(return_value=GkfeedCredentials("offline", "offline"))
        handler = cast(
            ItemEventHandler,
            SimpleNamespace(event=query, _gkfeed_credentials=credentials()),
        )
        await asyncio.wait_for(ItemEventHandler._handle_event(handler, "del", 1), 1)
        assert deleted.is_set()
        assert not task.done()
    finally:
        release.set()
        await task
    assert len(threads) == 4
    assert len(set(threads)) == 1


@pytest.mark.parametrize("media", ["audio", "video", "delayed_video"])
@pytest.mark.parametrize("blocked_stage", ["download", "exit"])
async def test_cancelled_download_finishes_before_cache_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    media: str,
    blocked_stage: str,
) -> None:
    started = threading.Event()
    release = threading.Event()
    closed = threading.Event()
    monkeypatch.setattr(CacheDir, "_CacheDir__base_path", str(tmp_path))
    monkeypatch.setattr(YtdlpDownloader, "_extract_info_sync", lambda url: METADATA)
    scheduled = AsyncMock()
    monkeypatch.setattr(Schedule, "run_task_after", scheduled)

    class Downloader:
        def __init__(self, opts: dict[str, Any]) -> None:
            self.output = Path(opts["outtmpl"])

        def __enter__(self) -> Self:
            return self

        def pause(self) -> None:
            started.set()
            assert release.wait(5)
            assert self.output.parent.is_dir()

        def download(self, url: str) -> None:
            if blocked_stage == "download":
                self.pause()
            self.output.write_bytes(b"video")

        def __exit__(self, *args: object) -> None:
            if blocked_stage == "exit":
                self.pause()
            assert self.output.read_bytes() == b"video"
            closed.set()

    monkeypatch.setattr(yt_dlp, "YoutubeDL", Downloader)

    async def download() -> None:
        context = (
            YtdlpDownloader.download_audio(URL)
            if media == "audio"
            else YtdlpDownloader.download_video(
                URL, cleanup_delay_minutes=5 if media == "delayed_video" else None
            )
        )
        async with context:
            pytest.fail("Cancelled download must not yield a file")

    task = asyncio.create_task(download())
    try:
        assert await asyncio.to_thread(started.wait, 5)
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        assert len(list(tmp_path.iterdir())) == 1
        scheduled.assert_not_awaited()
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert closed.is_set()
    if media == "delayed_video":
        scheduled.assert_awaited_once()
        assert scheduled.await_args is not None
        await scheduled.await_args.args[0].run()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("operation", ["info", "download"])
async def test_ytdlp_error_closes_context_and_propagates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    error = DownloadError("offline failure")
    closed: list[bool] = []

    class Downloader:
        def __init__(self, *args: Any) -> None:
            pass

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            closed.append(True)

        def extract_info(self, *args: Any, **kwargs: Any) -> None:
            raise error

        def download(self, *args: Any) -> None:
            raise error

    monkeypatch.setattr(yt_dlp, "YoutubeDL", Downloader)
    with pytest.raises(DownloadError) as raised:
        if operation == "info":
            await YtdlpDownloader._get_info(URL, DownloadSource.TIKTOK)
        else:
            await YtdlpDownloader._download_file(
                URL, {"outtmpl": str(tmp_path / "video.mp4")}, DownloadSource.TIKTOK
            )
    assert raised.value is error
    assert closed == [True]


async def test_cancelled_conversion_finishes_before_cache_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    started = threading.Event()
    release = threading.Event()
    monkeypatch.setattr(CacheDir, "_CacheDir__base_path", str(tmp_path))
    monkeypatch.setattr(YtdlpDownloader, "_extract_info_sync", lambda url: METADATA)

    def download(url: str, opts: dict[str, Any]) -> str:
        Path(opts["outtmpl"]).write_bytes(b"downloaded")
        return opts["outtmpl"]

    monkeypatch.setattr(YtdlpDownloader, "_download_file_sync", download)

    def write(input_path: str, output_path: str) -> None:
        started.set()
        assert release.wait(5)
        assert Path(input_path).read_bytes() == b"downloaded"
        Path(output_path).write_bytes(b"converted")

    async def convert(input_path: str, output_path: str) -> None:
        await asyncio.to_thread(write, input_path, output_path)

    monkeypatch.setattr(FfmpegService, "convert_video", convert)

    async def get_video() -> None:
        async with YtdlpDownloader.download_video(URL):
            pytest.fail("Cancelled conversion must not yield a file")

    task = asyncio.create_task(get_video())
    try:
        assert await asyncio.to_thread(started.wait, 5)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        assert len(list(tmp_path.iterdir())) == 1
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert list(tmp_path.iterdir()) == []
