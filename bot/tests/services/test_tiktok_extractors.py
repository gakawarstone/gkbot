from typing import Any
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlsplit

import pytest

from services.http import HttpRequestError, HttpService
from services.tiktok.extractor import _EXTRACTORS, TikTokInfoExtractor
from services.tiktok.extractor.exceptions import SourceInfoExtractFailed
from services.tiktok.extractor.tikwm import TikWm
from services.tiktok.extractor.ttdownloader import TTDownloader


@pytest.fixture
def slideshow_data() -> dict[str, Any]:
    return {
        "code": 0,
        "data": {
            "play": "https://cdn.example/soundtrack",
            "music": "/music/soundtrack",
            "music_info": {"play": "https://cdn.example/music"},
            "duration": 30,
            "images": ["https://cdn.example/1.jpg", "https://cdn.example/2.jpg"],
        },
    }


async def test_tikwm_extracts_slides_and_music(
    monkeypatch: pytest.MonkeyPatch, slideshow_data: dict[str, Any]
) -> None:
    get_json = AsyncMock(return_value=slideshow_data)
    monkeypatch.setattr(HttpService, "get_json", get_json)
    url = "https://www.tiktok.com/@user/photo/123?first=1&second=2"
    info = await TikWm().get_video_info(url)

    assert get_json.await_args is not None
    assert parse_qs(urlsplit(get_json.await_args.args[0]).query) == {"url": [url]}
    assert info.video_url is None
    assert info.images_urls == slideshow_data["data"]["images"]
    assert info.music_url == "https://cdn.example/music"
    assert info.duration is None


async def test_tikwm_video_supports_relative_media_urls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        HttpService,
        "get_json",
        AsyncMock(
            return_value={"code": 0, "data": {"play": "/video.mp4", "duration": 12}}
        ),
    )
    extractor = TikWm()
    info = await extractor.get_video_info("https://vt.tiktok.com/video/")
    assert info.video_url == "https://www.tikwm.com/video.mp4"
    assert info.images_urls == []
    assert info.music_url is None
    assert info.duration == 12
    assert (
        await extractor.get_video_file_url("https://vt.tiktok.com/video/")
        == info.video_url
    )


@pytest.mark.parametrize(
    "data",
    [
        {"code": -1, "msg": "Download failed"},
        {"code": 0, "data": None},
        {"code": 0, "data": {}},
        {"code": 0, "data": {"play": ""}},
        {"code": 0, "data": {"images": [None]}},
    ],
)
async def test_tikwm_invalid_responses_allow_fallback(
    monkeypatch: pytest.MonkeyPatch, data: dict[str, Any]
) -> None:
    monkeypatch.setattr(HttpService, "get_json", AsyncMock(return_value=data))
    with pytest.raises(SourceInfoExtractFailed):
        await TikWm().get_video_info("https://vt.tiktok.com/invalid/")


async def test_tikwm_network_failure_allows_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        HttpService, "get_json", AsyncMock(side_effect=HttpRequestError)
    )
    with pytest.raises(SourceInfoExtractFailed):
        await TikWm().get_video_info("https://vt.tiktok.com/invalid/")


async def test_tikwm_does_not_return_photo_soundtrack_as_video_url(
    monkeypatch: pytest.MonkeyPatch, slideshow_data: dict[str, Any]
) -> None:
    monkeypatch.setattr(HttpService, "get_json", AsyncMock(return_value=slideshow_data))
    with pytest.raises(SourceInfoExtractFailed):
        await TikWm().get_video_file_url("https://vt.tiktok.com/slideshow/")


async def test_slideshow_falls_back_to_tikwm_before_ttdownloader(
    monkeypatch: pytest.MonkeyPatch, slideshow_data: dict[str, Any]
) -> None:
    monkeypatch.setattr(HttpService, "get_json", AsyncMock(return_value=slideshow_data))
    downloaders: list[AsyncMock] = []
    for source in _EXTRACTORS:
        if not isinstance(source, TikWm):
            get_info = AsyncMock(side_effect=SourceInfoExtractFailed(source))
            monkeypatch.setattr(source, "get_video_info", get_info)
            if isinstance(source, TTDownloader):
                downloaders.append(get_info)

    info = await TikTokInfoExtractor.get_video_info("https://vt.tiktok.com/slideshow/")
    assert info.images_urls == slideshow_data["data"]["images"]
    assert info.video_url is None
    for downloader in downloaders:
        downloader.assert_not_awaited()


@pytest.mark.parametrize("method", ["get_video_info", "get_video_file_url"])
async def test_ttdownloader_rejects_photo_posts(
    monkeypatch: pytest.MonkeyPatch, method: str
) -> None:
    monkeypatch.setattr(
        HttpService,
        "get_redirected_url",
        AsyncMock(return_value="https://www.tiktok.com/@user/photo/123?share=1"),
    )
    extractor = TTDownloader()
    links = AsyncMock(return_value=["https://cdn.example/soundtrack"])
    monkeypatch.setattr(extractor, "_get_video_links", links)
    with pytest.raises(SourceInfoExtractFailed):
        await getattr(extractor, method)("https://vt.tiktok.com/slideshow/")
    links.assert_not_awaited()


async def test_ttdownloader_still_downloads_videos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        HttpService,
        "get_redirected_url",
        AsyncMock(return_value="https://www.tiktok.com/@user/video/123?share=1"),
    )
    extractor = TTDownloader()
    links = AsyncMock(return_value=["https://cdn.example/video.mp4"])
    monkeypatch.setattr(extractor, "_get_video_links", links)
    info = await extractor.get_video_info("https://vt.tiktok.com/video/")
    assert info.video_url == "https://cdn.example/video.mp4"
    links.assert_awaited_once_with("https://www.tiktok.com/@user/video/123")
