import asyncio
from pathlib import Path
from typing import cast
from unittest.mock import AsyncMock, Mock

import pytest
from aiogram.types import FSInputFile
from aiohttp import ClientConnectionError
from requests import ConnectionError as RequestsConnectionError
from yt_dlp.utils import DownloadError

from services.gallery_dl import (
    GalleryDlExtractionError,
    GalleryDlService,
    GalleryDlSlideshowInfo,
)
from services.http import HttpRequestError, HttpService
from services.tiktok.exceptions import (
    SerializationError,
    TikTokInfoExtractionFailed,
    TikTokInvalidUrl,
)
from services.tiktok.extractor import _EXTRACTORS, TikTokInfoExtractor
from services.tiktok.extractor._base import BaseExtractor, VideoUrlExtractor
from services.tiktok.extractor.api import ApiExtractor
from services.tiktok.extractor.exceptions import SourceInfoExtractFailed
from services.tiktok.extractor.gallery_dl import GalleryDl
from services.tiktok.extractor.mdown import Mdown
from services.tiktok.extractor.snaptik import Snaptik
from services.tiktok.extractor.tikdown import Tikdown
from services.tiktok.extractor.ttdownloader import TTDownloader
from services.tiktok.extractor.yt_dlp import YtDlp
from services.ytdlp import YtdlpDownloader
from services.ytdlp.downloader import _YtDlpInfo
from services.ytdlp.options_manager import YtDlpOptionsManager

URL = "https://vm.tiktok.com/short/"
FULL_URL = "https://www.tiktok.com/@photographer/video/123"
VIDEO_URL = "https://media.example/video.mp4"
MUSIC_URL = "https://media.example/music.mp3"
IMAGE_URL = "https://media.example/image.jpg"


@pytest.fixture(
    params=list({type(source): source for source in _EXTRACTORS}.values()),
    ids=lambda source: str(type(source).__name__),
)
def extractor(request: pytest.FixtureRequest) -> BaseExtractor:
    return cast(BaseExtractor, request.param)


@pytest.fixture
def provider_io(
    extractor: BaseExtractor, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> AsyncMock:
    """Stub provider I/O while exercising the real public extraction methods."""
    monkeypatch.setattr(
        HttpService, "get_redirected_url", AsyncMock(return_value=FULL_URL)
    )
    if isinstance(extractor, VideoUrlExtractor):
        operation = AsyncMock(return_value=[VIDEO_URL])
        monkeypatch.setattr(extractor, "_get_video_links", operation)
    elif isinstance(extractor, ApiExtractor):
        operation = AsyncMock(
            return_value={
                "data": {
                    "video": {
                        "play_addr": {"url_list": [VIDEO_URL]},
                        "height": 720,
                        "width": 1280,
                        "duration": 12999,
                    },
                    "music": {"play_url": {"url_list": [MUSIC_URL]}},
                }
            }
        )
        monkeypatch.setattr(HttpService, "get_json", operation)
    elif isinstance(extractor, GalleryDl):
        operation = AsyncMock(
            return_value=GalleryDlSlideshowInfo([IMAGE_URL], MUSIC_URL, 720, 1280, 12)
        )
        monkeypatch.setattr(GalleryDlService, "extract_slideshow_info", operation)
    else:
        assert isinstance(extractor, YtDlp)
        operation = AsyncMock(return_value=_YtDlpInfo(12, "title", 720, 1280))
        monkeypatch.setattr(YtdlpDownloader, "_get_info", operation)
        path = tmp_path / "cache" / "video.mp4"
        path.parent.mkdir()
        path.write_bytes(b"video")
        monkeypatch.setattr(
            YtdlpDownloader, "_download_file", AsyncMock(return_value=FSInputFile(path))
        )
        cache = Mock(delete_after=AsyncMock())
        monkeypatch.setattr(
            YtDlpOptionsManager, "choose_video_options", Mock(return_value=({}, cache))
        )
        monkeypatch.setattr(
            extractor, "_get_serveo_url", Mock(return_value="https://serve.example")
        )
    return operation


@pytest.mark.parametrize(
    "extractor",
    [Snaptik(), ApiExtractor("https://api.example"), GalleryDl(), YtDlp()],
    indirect=True,
)
async def test_provider_results_preserve_media(
    extractor: BaseExtractor, provider_io: AsyncMock
) -> None:
    info = await extractor.get_video_info(URL)
    if isinstance(extractor, VideoUrlExtractor):
        assert info.video_url == VIDEO_URL
    else:
        assert (info.height, info.width, info.duration) == (720, 1280, 12)
        if isinstance(extractor, ApiExtractor):
            assert info.video_url == VIDEO_URL
            assert info.music_url == MUSIC_URL
        elif isinstance(extractor, GalleryDl):
            assert info.images_urls == [IMAGE_URL]
            assert info.music_url == MUSIC_URL
        else:
            assert isinstance(info.video_input_file, FSInputFile)
            assert Path(info.video_input_file.path).read_bytes() == b"video"


@pytest.mark.parametrize("method", ["get_video_info", "get_video_file_url"])
@pytest.mark.parametrize(
    "error",
    [
        HttpRequestError(),
        ClientConnectionError(),
        TimeoutError(),
        ValueError(),
        IndexError(),
    ],
    ids=lambda error: type(error).__name__,
)
async def test_expected_failures_have_one_contract(
    monkeypatch: pytest.MonkeyPatch, method: str, error: Exception
) -> None:
    extractor = Snaptik()
    monkeypatch.setattr(extractor, "_get_video_links", AsyncMock(side_effect=error))
    with pytest.raises(SourceInfoExtractFailed) as raised:
        await getattr(extractor, method)(URL)
    assert raised.value.source is extractor
    assert raised.value.__cause__ is error


@pytest.mark.parametrize("method", ["get_video_info", "get_video_file_url"])
async def test_provider_specific_failures_use_the_same_contract(
    extractor: BaseExtractor, provider_io: AsyncMock, method: str
) -> None:
    if isinstance(extractor, (Mdown, TTDownloader)):
        error: Exception = RequestsConnectionError("provider unavailable")
    elif isinstance(extractor, ApiExtractor):
        error = SerializationError()
    elif isinstance(extractor, GalleryDl):
        error = GalleryDlExtractionError()
    elif isinstance(extractor, YtDlp):
        error = DownloadError("download failed")
    elif isinstance(extractor, Snaptik):
        error = TikTokInvalidUrl(URL)
    else:
        error = ValueError("malformed JSON")
    provider_io.side_effect = error
    with pytest.raises(SourceInfoExtractFailed) as raised:
        await getattr(extractor, method)(URL)
    assert raised.value.source is extractor
    assert raised.value.__cause__ is error


@pytest.mark.parametrize("method", ["get_video_info", "get_video_file_url"])
@pytest.mark.parametrize("error", [RuntimeError("bug"), asyncio.CancelledError()])
async def test_unexpected_errors_and_cancellation_propagate(
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    error: BaseException,
) -> None:
    extractor = Snaptik()
    monkeypatch.setattr(extractor, "_get_video_links", AsyncMock(side_effect=error))
    with pytest.raises(type(error)) as raised:
        await getattr(extractor, method)(URL)
    assert raised.value is error


async def test_legacy_url_entry_point(
    extractor: BaseExtractor, provider_io: AsyncMock
) -> None:
    if isinstance(extractor, GalleryDl):
        with pytest.raises(SourceInfoExtractFailed) as raised:
            await extractor.get_video_file_url(URL)
        assert raised.value.source is extractor
    elif isinstance(extractor, YtDlp):
        assert (await extractor.get_video_file_url(URL)).startswith(
            "https://serve.example/"
        )
    else:
        assert await extractor.get_video_file_url(URL) == VIDEO_URL
    provider_io.assert_awaited_once()


@pytest.mark.parametrize("links", [[], [""]])
async def test_missing_video_links_trigger_fallback(
    links: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = Snaptik()
    monkeypatch.setattr(source, "_get_video_links", AsyncMock(return_value=links))
    monkeypatch.setattr(
        HttpService, "get_redirected_url", AsyncMock(return_value=FULL_URL)
    )
    for method in (source.get_video_info, source.get_video_file_url):
        with pytest.raises(SourceInfoExtractFailed):
            await method(URL)


@pytest.mark.parametrize("method", ["get_video_info", "get_video_file_url"])
@pytest.mark.parametrize(
    "redirected, expected",
    [
        ("https://www.tiktok.com/@photographer/photo/123?share=photo#photo", FULL_URL),
        ("https://www.tiktok.com/@photographer/video/123?share=1", FULL_URL),
        (
            "https://photo.example/@photo/video/123",
            "https://photo.example/@photo/video/123",
        ),
    ],
)
@pytest.mark.parametrize("source_type", [GalleryDl, TTDownloader])
async def test_redirect_normalization_for_both_entry_points(
    source_type: type[BaseExtractor],
    method: str,
    redirected: str,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = source_type()
    redirect = AsyncMock(return_value=redirected)
    operation = AsyncMock(return_value={"video_url": VIDEO_URL})
    monkeypatch.setattr(HttpService, "get_redirected_url", redirect)
    monkeypatch.setattr(source, "_extract_video_data", operation)
    await getattr(source, method)(URL)
    redirect.assert_awaited_once_with(URL)
    operation.assert_awaited_once_with(expected)


@pytest.mark.parametrize("source_type", [GalleryDl, TTDownloader])
@pytest.mark.parametrize("method", ["get_video_info", "get_video_file_url"])
async def test_redirect_failure_uses_provider_failure_contract(
    source_type: type[BaseExtractor], method: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = source_type()
    error = HttpRequestError()
    monkeypatch.setattr(HttpService, "get_redirected_url", AsyncMock(side_effect=error))
    with pytest.raises(SourceInfoExtractFailed) as raised:
        await getattr(source, method)(URL)
    assert raised.value.source is source
    assert raised.value.__cause__ is error


@pytest.mark.parametrize("method", ["get_video_info", "get_video_url"])
async def test_fallback_continues_after_provider_failure(
    method: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extractor = Snaptik()
    monkeypatch.setattr(
        extractor, "_get_video_links", AsyncMock(side_effect=HttpRequestError())
    )
    final_source = Snaptik()
    monkeypatch.setattr(
        final_source, "_get_video_links", AsyncMock(return_value=[VIDEO_URL])
    )
    # The decorator retains this list, so mutate it in place for the test.
    original_sources = _EXTRACTORS[:]
    try:
        _EXTRACTORS[:] = [extractor, final_source]
        result = await getattr(TikTokInfoExtractor, method)(URL)
        assert (
            result == VIDEO_URL
            if method == "get_video_url"
            else result.video_url == VIDEO_URL
        )
        _EXTRACTORS[:] = [extractor]
        with pytest.raises(TikTokInfoExtractionFailed) as raised:
            await getattr(TikTokInfoExtractor, method)(URL)
        assert raised.value.url == URL
    finally:
        _EXTRACTORS[:] = original_sources


@pytest.mark.parametrize("method", ["get_video_info", "get_video_file_url"])
async def test_ytdlp_keeps_downloaded_file_after_context_exit(
    method: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = YtDlp()
    monkeypatch.setattr(
        source, "_get_serveo_url", Mock(return_value="https://serve.example")
    )
    monkeypatch.setattr(
        YtdlpDownloader,
        "_get_info",
        AsyncMock(return_value=_YtDlpInfo(12, "title", 720, 1280)),
    )
    path = tmp_path / "cache" / "video.mp4"
    path.parent.mkdir()
    path.write_bytes(b"video")
    file = FSInputFile(path)
    monkeypatch.setattr(YtdlpDownloader, "_download_file", AsyncMock(return_value=file))
    cache = Mock(delete_after=AsyncMock())
    monkeypatch.setattr(
        YtDlpOptionsManager, "choose_video_options", Mock(return_value=({}, cache))
    )
    result = await getattr(source, method)(URL)
    cache.delete.assert_not_called()
    cache.delete_after.assert_awaited_once_with(minutes=5)
    assert path.read_bytes() == b"video"
    if method == "get_video_info":
        assert result.video_input_file is file
    else:
        assert result == "https://serve.example/" + "/".join(path.parts[-3:])


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"data": None},
        {"data": {"video": []}},
        {"data": {"music": {"play_url": {"url_list": []}}}},
    ],
)
@pytest.mark.parametrize("method", ["get_video_info", "get_video_file_url"])
async def test_malformed_api_payload_uses_failure_contract(
    data: dict[str, object], method: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = ApiExtractor("https://api.example")
    monkeypatch.setattr(HttpService, "get_json", AsyncMock(return_value=data))
    with pytest.raises(SourceInfoExtractFailed) as raised:
        await getattr(source, method)(URL)
    assert raised.value.source is source
    assert isinstance(raised.value.__cause__, SerializationError)


@pytest.mark.parametrize(
    "video_url",
    [
        "https://media.example/music/123",
        "https://media.example/play?mime_type=audio_mpeg",
    ],
)
async def test_api_preserves_slideshow_and_filters_audio_video_url(
    video_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = ApiExtractor("https://api.example")
    monkeypatch.setattr(
        HttpService,
        "get_json",
        AsyncMock(
            return_value={
                "data": {
                    "image_post_info": {
                        "images": [{"display_image": {"url_list": [IMAGE_URL]}}]
                    },
                    "video": {"play_addr": {"url_list": [video_url]}},
                    "music": {"play_url": {"url_list": [MUSIC_URL]}},
                }
            }
        ),
    )
    info = await source.get_video_info(URL)
    assert not info.video_url
    assert info.video_input_file is None
    assert info.images_urls == [IMAGE_URL]
    assert info.music_url == MUSIC_URL
    with pytest.raises(SourceInfoExtractFailed):
        await source.get_video_file_url(URL)


@pytest.mark.parametrize(
    "payload", [b"not JSON", b"[]", b"null", b'{"status": true}', b'{"status": false}']
)
@pytest.mark.parametrize("method", ["get_video_info", "get_video_file_url"])
async def test_tikdown_malformed_payload_uses_failure_contract(
    payload: bytes, method: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = Tikdown()
    monkeypatch.setattr(
        HttpService,
        "get",
        AsyncMock(return_value=b'<input type="hidden" value="token">'),
    )
    monkeypatch.setattr(HttpService, "post", AsyncMock(return_value=payload))
    with pytest.raises(SourceInfoExtractFailed) as raised:
        await getattr(source, method)(URL)
    assert raised.value.source is source


@pytest.mark.parametrize(
    "payload", [b"Error: invalid URL", b"error_api_web;", b"changed page markup"]
)
@pytest.mark.parametrize("method", ["get_video_info", "get_video_file_url"])
async def test_snaptik_malformed_payload_uses_failure_contract(
    payload: bytes, method: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = Snaptik()
    monkeypatch.setattr(HttpService, "get", AsyncMock(return_value=b""))
    monkeypatch.setattr(HttpService, "post", AsyncMock(return_value=payload))
    with pytest.raises(SourceInfoExtractFailed) as raised:
        await getattr(source, method)(URL)
    assert raised.value.source is source


async def test_ytdlp_without_serveo_skips_download_and_uses_failure_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = YtDlp()
    monkeypatch.setattr(source, "_get_serveo_url", Mock(return_value=None))
    download = Mock()
    monkeypatch.setattr(YtdlpDownloader, "download_video", download)
    with pytest.raises(SourceInfoExtractFailed) as raised:
        await source.get_video_file_url(URL)
    assert raised.value.source is source
    download.assert_not_called()
