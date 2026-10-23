from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import FSInputFile

from services.ffmpeg import FfmpegService
from services.tiktok import TikTokService
from services.tiktok.extractor import TikTokInfoExtractor
from services.tiktok.extractor.yt_dlp import YtDlp
from services.ytdlp import YtdlpDownloader
from services.ytdlp._types import VideoFileInfo
from services.ytdlp.options_manager import YtDlpOptionsManager


@pytest.mark.parametrize("worker", [False, True])
async def test_extracts_presentation_from_local_and_worker_metadata(
    monkeypatch: pytest.MonkeyPatch, worker: bool
) -> None:
    raw_info = {
        "title": "title",
        "duration": 60,
        "height": 720,
        "width": 1280,
        "thumbnail": "https://example.com/cover.jpg",
        "start_time": 12.7,
        "timestamp": 1700000000,
    }
    get_info = AsyncMock(return_value=raw_info)
    monkeypatch.setattr("services.ytdlp.downloader.get_info", get_info)
    ydl = MagicMock()
    ydl.__enter__.return_value.extract_info.return_value = raw_info
    monkeypatch.setattr(
        "services.ytdlp.downloader.yt_dlp.YoutubeDL", MagicMock(return_value=ydl)
    )
    url = (
        "https://www.youtube.com/shorts/id?t=12"
        if worker
        else "https://example.com/video"
    )
    info = await YtdlpDownloader._get_info(url)
    assert info.cover == raw_info["thumbnail"]
    assert info.start_timestamp == 12
    assert get_info.await_count == int(worker)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            {
                "thumbnail": "https://example.com/cover.webp",
                "thumbnails": [
                    {"url": "https://example.com/small.jpg"},
                    {"url": "https://example.com/large.jpg"},
                    {
                        "url": "https://example.com/private.jpg",
                        "http_headers": {"Cookie": "private"},
                    },
                ],
            },
            "https://example.com/large.jpg",
        ),
        ({"thumbnail": {}, "thumbnails": None}, None),
        (
            {
                "thumbnail": "https://example.com/private.jpg",
                "thumbnails": [
                    {
                        "url": "https://example.com/private.jpg",
                        "http_headers": {"Cookie": "private"},
                    }
                ],
            },
            None,
        ),
        ({"thumbnails": [None, 123, {"url": "data:image/jpeg,123"}]}, None),
    ],
)
def test_selects_supported_cover(raw: dict[str, Any], expected: str | None) -> None:
    assert YtdlpDownloader._get_cover(raw) == expected


@pytest.mark.parametrize("edited", [False, True])
async def test_download_keeps_metadata_through_probe_and_omits_start_for_edits(
    monkeypatch: pytest.MonkeyPatch, edited: bool
) -> None:
    monkeypatch.setattr(
        "services.ytdlp.downloader.get_info",
        AsyncMock(
            return_value={
                "title": "title",
                "thumbnail": "https://example.com/cover.jpg",
                "start_time": 12,
            }
        ),
    )
    cache = MagicMock()
    options = (
        {"postprocessors": [{"remove_sponsor_segments": ["sponsor"]}]} if edited else {}
    )
    monkeypatch.setattr(
        YtDlpOptionsManager,
        "choose_video_options",
        MagicMock(return_value=(options, cache)),
    )
    monkeypatch.setattr(
        YtdlpDownloader,
        "_download_file",
        AsyncMock(return_value=FSInputFile("video.mp4")),
    )
    monkeypatch.setattr(
        FfmpegService,
        "get_video_metadata",
        AsyncMock(
            return_value={
                "duration": 60,
                "height": 720,
                "width": 1280,
            }
        ),
    )
    async with YtdlpDownloader.download_video(
        "https://www.youtube.com/shorts/id"
    ) as video:
        assert (video.duration, video.height, video.width) == (60, 720, 1280)
        assert video.cover == "https://example.com/cover.jpg"
        assert video.start_timestamp == (None if edited else 12)
        cache.delete.assert_not_called()
    cache.delete.assert_called_once_with()


async def test_tiktok_ytdlp_metadata_reaches_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file = FSInputFile("video.mp4")
    video = VideoFileInfo(
        file,
        720,
        1280,
        60,
        "title",
        cover="https://example.com/cover.jpg",
        start_timestamp=12,
    )

    @asynccontextmanager
    async def download(
        url: str, cleanup_delay_minutes: int
    ) -> AsyncIterator[VideoFileInfo]:
        assert cleanup_delay_minutes == 5
        yield video

    monkeypatch.setattr(YtdlpDownloader, "download_video", download)
    info = await YtDlp().get_video_info("https://www.tiktok.com/@user/video/1")
    monkeypatch.setattr(
        TikTokInfoExtractor, "get_video_info", AsyncMock(return_value=info)
    )
    result = await TikTokService.get_video("https://www.tiktok.com/@user/video/1")
    assert result.input_file is file
    assert result.send_options(result.duration) == {
        "cover": video.cover,
        "start_timestamp": 12,
    }


@pytest.mark.parametrize(
    "offset", [None, "12", True, -1, float("nan"), float("inf"), 60]
)
async def test_optional_bad_metadata_does_not_fail_extraction(
    monkeypatch: pytest.MonkeyPatch, offset: object
) -> None:
    monkeypatch.setattr(
        "services.ytdlp.downloader.get_info",
        AsyncMock(
            return_value={
                "title": "title",
                "duration": 60,
                "thumbnail": [],
                "thumbnails": "bad",
                "start_time": offset,
                "timestamp": 1700000000,
            }
        ),
    )
    info = await YtdlpDownloader._get_info("https://www.youtube.com/shorts/id")
    assert info.cover is None
    assert info.start_timestamp is None
