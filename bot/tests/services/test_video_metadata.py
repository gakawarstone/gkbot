import pytest
from aiogram.types import BufferedInputFile

from services.video import VideoMetadata, cover_url, start_timestamp
from services.ytdlp._types import VideoFileInfo


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        123,
        "file:///tmp/cover.jpg",
        "https://example.com/cover.webp",
        "https:///cover.jpg",
        "https://user:pass@example.com/cover.jpg",
        "https://example.com:bad/cover.jpg",
        "https://[invalid/cover.jpg",
        "https://example.com/cover.jpg\n",
    ],
)
def test_invalid_cover_urls_are_omitted(value: object) -> None:
    assert cover_url(value) is None


@pytest.mark.parametrize("extension", ["jpg", "jpeg", "PNG"])
def test_cover_urls_keep_signed_queries(extension: str) -> None:
    url = f"https://example.com/cover.{extension}?signature=123"
    assert cover_url(url) == url


@pytest.mark.parametrize(
    "value",
    [None, "12", True, -1, float("nan"), float("inf"), 2**10000, 100, 101],
)
def test_invalid_start_times_are_omitted(value: object) -> None:
    assert start_timestamp(value, 100) is None


@pytest.mark.parametrize(("value", "expected"), [(0, 0), (12.9, 12), (99, 99)])
def test_start_time_is_seconds(value: float, expected: int) -> None:
    assert start_timestamp(value, 100) == expected


def test_video_model_defaults_preserve_old_constructor() -> None:
    video = VideoFileInfo(
        BufferedInputFile(b"video", "video.mp4"), 720, 1280, 30, "title"
    )
    assert video.cover is None
    assert video.start_timestamp is None
    assert video.send_options(video.duration) == {}


def test_uploaded_cover_and_timestamp_are_sendable() -> None:
    cover = BufferedInputFile(b"cover", "cover.jpg")
    metadata = VideoMetadata(cover=cover, start_timestamp=12)
    assert metadata.send_options(30) == {"cover": cover, "start_timestamp": 12}
    assert metadata.send_options(10) == {"cover": cover}
