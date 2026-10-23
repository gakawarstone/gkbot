from asyncio import CancelledError
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, FSInputFile, InaccessibleMessage, Message

from handlers.button.pornhub.download import download as download_pornhub
from handlers.button.porno365.download import download as download_porno365
from handlers.button.vk.download import download as download_vk
from handlers.button.youtube.download import download as download_youtube
from services.porno365 import Porno365Service
from services.youtube import YoutubeApiService, YoutubeVideoData
from services.ytdlp import YtdlpDownloader
from services.ytdlp._types import AudioFileInfo, VideoFileInfo


@dataclass(frozen=True)
class Source:
    download: Callable[[CallbackQuery], Awaitable[None]]
    prefix: str
    identifier: str
    url: str
    require_callback: bool = False

    def payload(self, event: str = "dlmp4", status: str = "False") -> str:
        return f"{self.prefix}:{event}:{status}:{self.identifier}"


SOURCES = [
    Source(
        download_youtube,
        "ytbtn",
        "oRxuDeZRFx8",
        "https://www.youtube.com/watch?v=oRxuDeZRFx8",
    ),
    Source(
        download_vk,
        "vkbtn",
        "video-50883936_456244451",
        "https://vk.com/video-50883936_456244451",
        require_callback=True,
    ),
    Source(
        download_pornhub,
        "phbtn",
        "ph123",
        "https://www.pornhub.com/view_video.php?viewkey=ph123",
    ),
    Source(
        download_porno365,
        "p365btn",
        "https://porno365.example/video/123",
        "https://cdn.example/video.mp4",
    ),
]


@pytest.fixture(params=SOURCES, ids=lambda source: source.prefix)
def source(request: pytest.FixtureRequest) -> Source:
    return request.param


@dataclass
class DownloadMocks:
    callback: MagicMock
    message: MagicMock
    status: MagicMock
    audio: AudioFileInfo
    video: VideoFileInfo
    audio_context: MagicMock
    video_context: MagicMock
    download_audio: MagicMock
    download_video: MagicMock
    metadata: AsyncMock
    resolve_url: AsyncMock


@pytest.fixture
def mocks(monkeypatch: pytest.MonkeyPatch) -> DownloadMocks:
    message = MagicMock(spec=Message)
    status = MagicMock(spec=Message)
    message.answer = AsyncMock(return_value=status)
    message.edit_text = AsyncMock()
    message.delete = AsyncMock()
    message.answer_audio = AsyncMock()
    message.answer_video = AsyncMock()
    status.delete = AsyncMock()
    callback = MagicMock(spec=CallbackQuery, message=message)

    audio = AudioFileInfo(FSInputFile("audio.mp3"), duration=123, title="Audio title")
    video = VideoFileInfo(
        FSInputFile("video.mp4"),
        height=720,
        width=1280,
        duration=456,
        title="Video title",
    )
    audio_context = MagicMock()
    audio_context.__aenter__ = AsyncMock(return_value=audio)
    audio_context.__aexit__ = AsyncMock(return_value=False)
    video_context = MagicMock()
    video_context.__aenter__ = AsyncMock(return_value=video)
    video_context.__aexit__ = AsyncMock(return_value=False)
    download_audio = MagicMock(return_value=audio_context)
    download_video = MagicMock(return_value=video_context)
    monkeypatch.setattr(YtdlpDownloader, "download_audio", download_audio)
    monkeypatch.setattr(YtdlpDownloader, "download_video", download_video)
    metadata = AsyncMock(
        return_value=YoutubeVideoData(
            title="API title",
            channel_title="Channel🔥",
            thumbnail_url="https://example.com/thumb.jpg",
        )
    )
    resolve_url = AsyncMock(return_value="https://cdn.example/video.mp4")
    monkeypatch.setattr(YoutubeApiService, "get_video_data", metadata)
    monkeypatch.setattr(Porno365Service, "get_best_video_url", resolve_url)
    return DownloadMocks(
        callback,
        message,
        status,
        audio,
        video,
        audio_context,
        video_context,
        download_audio,
        download_video,
        metadata,
        resolve_url,
    )


@pytest.mark.parametrize("reuse_status", [False, True])
async def test_video_contract(
    source: Source, mocks: DownloadMocks, reuse_status: bool
) -> None:
    mocks.callback.data = source.payload(status=str(reuse_status))

    await source.download(mocks.callback)

    mocks.download_video.assert_called_once_with(source.url)
    mocks.download_audio.assert_not_called()
    mocks.video_context.__aexit__.assert_awaited_once_with(None, None, None)
    mocks.message.answer_video.assert_awaited_once()
    call = mocks.message.answer_video.await_args
    assert call is not None
    options = call.kwargs.copy()
    assert call.args == (mocks.video.input_file,)
    expected: dict[str, object] = {
        "height": 720,
        "width": 1280,
        "duration": 456,
        "supports_streaming": True,
    }
    if source.prefix == "ytbtn":
        mocks.metadata.assert_awaited_once_with(source.url)
        thumbnail = options.pop("thumbnail")
        assert thumbnail.url == "https://example.com/thumb.jpg"
        expected["caption"] = (
            f'<b>Video title</b>\n\n<a href="{source.url}">Channel</a>'
        )
    else:
        mocks.metadata.assert_not_awaited()
    if source.prefix in {"phbtn", "p365btn"}:
        expected["has_spoiler"] = True
    assert options == expected
    if source.prefix == "p365btn":
        mocks.resolve_url.assert_awaited_once_with(source.identifier)
    else:
        mocks.resolve_url.assert_not_awaited()

    if reuse_status:
        mocks.message.answer.assert_not_awaited()
        mocks.message.edit_text.assert_awaited_once_with("Cкачиваю " + source.url)
        mocks.message.delete.assert_awaited_once()
        mocks.status.delete.assert_not_awaited()
    else:
        mocks.message.answer.assert_awaited_once_with("Cкачиваю " + source.url)
        mocks.message.edit_text.assert_not_awaited()
        mocks.status.delete.assert_awaited_once()
        mocks.message.delete.assert_not_awaited()


@pytest.mark.parametrize("source", SOURCES[:2], ids=lambda source: source.prefix)
@pytest.mark.parametrize("reuse_status", [False, True])
async def test_audio_contract(
    source: Source, mocks: DownloadMocks, reuse_status: bool
) -> None:
    mocks.callback.data = source.payload("dlmp3", str(reuse_status))

    await source.download(mocks.callback)

    mocks.download_audio.assert_called_once_with(source.url)
    mocks.download_video.assert_not_called()
    mocks.audio_context.__aexit__.assert_awaited_once_with(None, None, None)
    mocks.message.answer_audio.assert_awaited_once_with(
        audio=mocks.audio.input_file,
        title="Audio title",
        performer="GKBOT",
        duration=123,
    )
    mocks.message.answer_video.assert_not_awaited()
    mocks.metadata.assert_not_awaited()
    status = mocks.message if reuse_status else mocks.status
    status.delete.assert_awaited_once()


@pytest.mark.parametrize("missing", ["message", "inaccessible_message", "data"])
async def test_missing_callback_contract(
    source: Source, mocks: DownloadMocks, missing: str
) -> None:
    mocks.callback.data = source.payload()
    if missing == "message":
        mocks.callback.message = None
    elif missing == "inaccessible_message":
        mocks.callback.message = MagicMock(spec=InaccessibleMessage)
    else:
        mocks.callback.data = None

    if source.require_callback:
        with pytest.raises(ValueError, match="Callback"):
            await source.download(mocks.callback)
    else:
        await source.download(mocks.callback)

    mocks.message.answer.assert_not_awaited()
    mocks.download_audio.assert_not_called()
    mocks.download_video.assert_not_called()
    mocks.resolve_url.assert_not_awaited()


async def test_malformed_callback_contract(
    source: Source, mocks: DownloadMocks
) -> None:
    mocks.callback.data = source.prefix + ":dlmp4"
    with pytest.raises(ValueError):
        await source.download(mocks.callback)
    mocks.message.answer.assert_not_awaited()
    mocks.download_video.assert_not_called()


async def test_unknown_event_contract(source: Source, mocks: DownloadMocks) -> None:
    mocks.callback.data = source.payload("unknown")
    await source.download(mocks.callback)
    mocks.download_audio.assert_not_called()
    mocks.download_video.assert_not_called()
    mocks.message.answer.assert_awaited_once_with("Cкачиваю " + source.url)
    mocks.status.delete.assert_awaited_once()


async def test_legacy_status_flag_contract(
    source: Source, mocks: DownloadMocks
) -> None:
    mocks.callback.data = source.payload(status="1")
    await source.download(mocks.callback)
    mocks.message.answer.assert_not_awaited()
    mocks.message.edit_text.assert_awaited_once_with("Cкачиваю " + source.url)
    mocks.message.delete.assert_awaited_once()


@pytest.mark.parametrize("reuse_status", [False, True])
@pytest.mark.parametrize("failure", ["download", "send", "cleanup"])
async def test_failure_cleans_status(
    source: Source, mocks: DownloadMocks, reuse_status: bool, failure: str
) -> None:
    mocks.callback.data = source.payload(status=str(reuse_status))
    error = RuntimeError("download lifecycle failure")
    if failure == "download":
        mocks.video_context.__aenter__.side_effect = error
    elif failure == "send":
        mocks.message.answer_video.side_effect = error
    else:
        mocks.video_context.__aexit__.side_effect = error

    with pytest.raises(RuntimeError) as raised:
        await source.download(mocks.callback)

    assert raised.value is error
    status = mocks.message if reuse_status else mocks.status
    status.delete.assert_awaited_once()
    if failure != "download":
        mocks.video_context.__aexit__.assert_awaited_once()


async def test_youtube_metadata_failure_cleans_download_and_status(
    mocks: DownloadMocks,
) -> None:
    source = SOURCES[0]
    mocks.callback.data = source.payload()
    mocks.metadata.side_effect = ValueError("metadata unavailable")
    with pytest.raises(ValueError, match="metadata unavailable"):
        await source.download(mocks.callback)
    mocks.message.answer_video.assert_not_awaited()
    mocks.video_context.__aexit__.assert_awaited_once()
    mocks.status.delete.assert_awaited_once()


async def test_porno365_resolution_failure_precedes_status(
    mocks: DownloadMocks,
) -> None:
    source = SOURCES[3]
    mocks.callback.data = source.payload()
    mocks.resolve_url.side_effect = ValueError("video unavailable")
    with pytest.raises(ValueError, match="video unavailable"):
        await source.download(mocks.callback)
    mocks.message.answer.assert_not_awaited()
    mocks.download_video.assert_not_called()


@pytest.mark.parametrize("source", SOURCES[:2], ids=lambda source: source.prefix)
@pytest.mark.parametrize("failure", ["download", "send"])
async def test_audio_failure_cleans_status(
    source: Source, mocks: DownloadMocks, failure: str
) -> None:
    mocks.callback.data = source.payload("dlmp3")
    error = RuntimeError("audio failure")
    if failure == "download":
        mocks.audio_context.__aenter__.side_effect = error
    else:
        mocks.message.answer_audio.side_effect = error
    with pytest.raises(RuntimeError) as raised:
        await source.download(mocks.callback)
    assert raised.value is error
    mocks.status.delete.assert_awaited_once()
    if failure == "send":
        mocks.audio_context.__aexit__.assert_awaited_once()


async def test_cancellation_cleans_download_and_status(
    source: Source, mocks: DownloadMocks
) -> None:
    mocks.callback.data = source.payload()
    mocks.message.answer_video.side_effect = CancelledError()
    with pytest.raises(CancelledError):
        await source.download(mocks.callback)
    mocks.video_context.__aexit__.assert_awaited_once()
    mocks.status.delete.assert_awaited_once()


@pytest.mark.parametrize("source", SOURCES[2:], ids=lambda source: source.prefix)
async def test_video_only_sources_ignore_audio(
    source: Source, mocks: DownloadMocks
) -> None:
    mocks.callback.data = source.payload("dlmp3")
    await source.download(mocks.callback)
    mocks.download_audio.assert_not_called()
    mocks.download_video.assert_not_called()
    mocks.status.delete.assert_awaited_once()


@pytest.mark.parametrize(
    ("identifier", "url"),
    [
        ("https://vk.cc/abc", "https://vk.cc/abc"),
        ("wall-123", "https://vk.com/wall-123"),
    ],
)
async def test_vk_legacy_url_forms(
    mocks: DownloadMocks, identifier: str, url: str
) -> None:
    mocks.callback.data = f"vkbtn:dlmp4:False:{identifier}"
    await download_vk(mocks.callback)
    mocks.download_video.assert_called_once_with(url)
