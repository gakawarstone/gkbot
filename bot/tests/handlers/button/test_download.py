"""Contract tests for all source adapters, without Telegram or network requests."""

from asyncio import CancelledError
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from importlib import import_module
from typing import Literal, cast
from unittest.mock import AsyncMock, Mock

import pytest
from aiogram import Router
from aiogram.methods import DeleteEphemeralMessage, SendMessage
from aiogram.types import (
    CallbackQuery,
    Chat,
    InaccessibleMessage,
    Message,
    URLInputFile,
)

from handlers.button.download import YtdlpDownloader
from services.porno365 import Porno365Service
from services.youtube import YoutubeApiService, YoutubeVideoData
from services.ytdlp._types import AudioFileInfo, VideoFileInfo
from tests.handlers import CallbackEvent
from tests.mocks.message import make_fake_callback
from tests.mocks.status import StatusHarness

from ... import integration_test


@dataclass(frozen=True)
class DownloadCase:
    source: str
    prefix: str
    identifier: str
    url: str
    media_type: Literal["audio", "video"] = "video"

    def payload(self, reuse_status: bool = False, event: str | None = None) -> str:
        if event is None:
            event = "dlmp3" if self.media_type == "audio" else "dlmp4"
        return f"{self.prefix}:{event}:{reuse_status}:{self.identifier}"


VIDEO_CASES = [
    DownloadCase(
        "youtube", "ytbtn", "oRxuDeZRFx8", "https://www.youtube.com/watch?v=oRxuDeZRFx8"
    ),
    DownloadCase(
        "vk",
        "vkbtn",
        "video-50883936_456244451",
        "https://vk.com/video-50883936_456244451",
    ),
    DownloadCase(
        "pornhub",
        "phbtn",
        "ph123",
        "https://www.pornhub.com/view_video.php?viewkey=ph123",
    ),
    DownloadCase(
        "porno365",
        "p365btn",
        "https://porno365.example/video/123",
        "https://cdn.example/video.mp4",
    ),
]
AUDIO_CASES = [
    DownloadCase(case.source, case.prefix, case.identifier, case.url, "audio")
    for case in VIDEO_CASES[:2]
]
CASES = VIDEO_CASES + AUDIO_CASES


class DownloadHarness:
    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.status = Mock(spec=Message, delete=AsyncMock(), ephemeral_message_id=None)
        self.message = Mock(
            spec=Message,
            chat=Chat(id=42, type="private"),
            ephemeral_message_id=None,
            answer=AsyncMock(return_value=self.status),
            edit_text=AsyncMock(),
            delete=AsyncMock(),
            answer_audio=AsyncMock(),
            answer_video=AsyncMock(),
        )
        self.audio = AudioFileInfo(
            URLInputFile("https://cdn.example/audio.mp3"), 42, "Audio"
        )
        self.video = VideoFileInfo(
            URLInputFile("https://cdn.example/video.mp4"), 720, 1280, 42, "Video"
        )
        self.start_audio = AsyncMock()
        self.start_video = AsyncMock()
        self.exit_audio = AsyncMock()
        self.exit_video = AsyncMock()
        monkeypatch.setattr(YtdlpDownloader, "download_audio", self.download_audio)
        monkeypatch.setattr(YtdlpDownloader, "download_video", self.download_video)
        self.metadata = AsyncMock(
            return_value=YoutubeVideoData(
                "Unused", "Channel🔥", "https://img.example/thumb.jpg"
            )
        )
        self.resolve_url = AsyncMock(return_value=VIDEO_CASES[3].url)
        monkeypatch.setattr(YoutubeApiService, "get_video_data", self.metadata)
        monkeypatch.setattr(Porno365Service, "get_best_video_url", self.resolve_url)

    def callback(self, payload: str | None) -> CallbackQuery:
        return make_fake_callback("").model_copy(
            update={"data": payload, "message": self.message}
        )

    @asynccontextmanager
    async def download_audio(self, url: str) -> AsyncIterator[AudioFileInfo]:
        try:
            await self.start_audio(url)
            yield self.audio
        finally:
            await self.exit_audio()

    @asynccontextmanager
    async def download_video(self, url: str) -> AsyncIterator[VideoFileInfo]:
        try:
            await self.start_video(url)
            yield self.video
        finally:
            await self.exit_video()


@pytest.fixture
def harness(monkeypatch: pytest.MonkeyPatch) -> DownloadHarness:
    return DownloadHarness(monkeypatch)


@pytest.mark.parametrize(
    "case", CASES, ids=lambda case: f"{case.source}-{case.media_type}"
)
@pytest.mark.parametrize("reuse_status", [False, True])
async def test_download_contract(
    case: DownloadCase, reuse_status: bool, harness: DownloadHarness
) -> None:
    async def assert_context_active(*args: object, **kwargs: object) -> None:
        harness.exit_audio.assert_not_awaited()
        harness.exit_video.assert_not_awaited()

    harness.message.answer_audio.side_effect = assert_context_active
    harness.message.answer_video.side_effect = assert_context_active
    handler = import_module(f"handlers.button.{case.source}.download")
    await handler.download(harness.callback(case.payload(reuse_status)))

    status_text = "Cкачиваю " + case.url
    if reuse_status:
        harness.message.edit_text.assert_awaited_once_with(status_text)
        harness.message.answer.assert_not_awaited()
        harness.message.delete.assert_awaited_once_with()
        harness.status.delete.assert_not_awaited()
    else:
        harness.message.answer.assert_awaited_once_with(status_text)
        harness.message.edit_text.assert_not_awaited()
        harness.status.delete.assert_awaited_once_with()
        harness.message.delete.assert_not_awaited()

    if case.media_type == "audio":
        harness.start_audio.assert_awaited_once_with(case.url)
        harness.exit_audio.assert_awaited_once_with()
        harness.start_video.assert_not_awaited()
        harness.message.answer_video.assert_not_awaited()
        harness.message.answer_audio.assert_awaited_once_with(
            audio=harness.audio.input_file,
            title="Audio",
            performer="GKBOT",
            duration=42,
        )
    else:
        harness.start_video.assert_awaited_once_with(case.url)
        harness.exit_video.assert_awaited_once_with()
        harness.start_audio.assert_not_awaited()
        harness.message.answer_audio.assert_not_awaited()
        options: dict[str, object] = {}
        if case.source == "youtube":
            harness.metadata.assert_awaited_once_with(case.url)
            options["caption"] = f'<b>Video</b>\n\n<a href="{case.url}">Channel</a>'
            sent_video = harness.message.answer_video.await_args
            assert sent_video is not None
            thumbnail = sent_video.kwargs["thumbnail"]
            assert isinstance(thumbnail, URLInputFile)
            assert thumbnail.url == "https://img.example/thumb.jpg"
            options["thumbnail"] = thumbnail
        elif case.source in {"pornhub", "porno365"}:
            options["has_spoiler"] = True
        harness.message.answer_video.assert_awaited_once_with(
            harness.video.input_file,
            height=720,
            width=1280,
            duration=42,
            supports_streaming=True,
            **options,
        )
    if case.source != "youtube" or case.media_type != "video":
        harness.metadata.assert_not_awaited()
    if case.source == "porno365":
        harness.resolve_url.assert_awaited_once_with(case.identifier)
    else:
        harness.resolve_url.assert_not_awaited()


@pytest.mark.parametrize("case", VIDEO_CASES, ids=lambda case: case.source)
@pytest.mark.parametrize("invalid", ["no-message", "inaccessible", "no-data"])
async def test_invalid_callback(
    case: DownloadCase, invalid: str, harness: DownloadHarness
) -> None:
    callback = harness.callback(case.payload())
    error = "Callback message is inaccessible or None"
    if invalid == "no-message":
        callback = callback.model_copy(update={"message": None})
    elif invalid == "inaccessible":
        inaccessible = InaccessibleMessage(
            chat=Chat(id=42, type="private"), message_id=1, date=0
        )
        callback = callback.model_copy(update={"message": inaccessible})
    else:
        callback = callback.model_copy(update={"data": None})
        error = "Callback data cannot be None"
    handler = import_module(f"handlers.button.{case.source}.download")
    if case.source == "vk":
        with pytest.raises(ValueError, match=error):
            await handler.download(callback)
    else:
        await handler.download(callback)
    harness.message.answer.assert_not_awaited()
    harness.message.edit_text.assert_not_awaited()
    harness.start_audio.assert_not_awaited()
    harness.start_video.assert_not_awaited()
    harness.resolve_url.assert_not_awaited()


@pytest.mark.parametrize("case", VIDEO_CASES, ids=lambda case: case.source)
async def test_malformed_payload_fails_before_status(
    case: DownloadCase, harness: DownloadHarness
) -> None:
    handler = import_module(f"handlers.button.{case.source}.download")
    with pytest.raises(ValueError):
        await handler.download(harness.callback(case.prefix + ":dlmp4"))
    harness.message.answer.assert_not_awaited()
    harness.message.edit_text.assert_not_awaited()
    harness.resolve_url.assert_not_awaited()


@pytest.mark.parametrize("case", VIDEO_CASES, ids=lambda case: case.source)
async def test_unknown_event_preserves_status_only_path(
    case: DownloadCase, harness: DownloadHarness
) -> None:
    handler = import_module(f"handlers.button.{case.source}.download")
    await handler.download(harness.callback(case.payload(event="unknown")))
    harness.message.answer.assert_awaited_once_with("Cкачиваю " + case.url)
    harness.status.delete.assert_awaited_once_with()
    harness.start_audio.assert_not_awaited()
    harness.start_video.assert_not_awaited()


@pytest.mark.parametrize(
    "case", CASES, ids=lambda case: f"{case.source}-{case.media_type}"
)
@pytest.mark.parametrize("failure", ["download", "send"])
@pytest.mark.parametrize("reuse_status", [False, True])
async def test_failure_cleans_media_and_status(
    case: DownloadCase, failure: str, reuse_status: bool, harness: DownloadHarness
) -> None:
    if failure == "download":
        operation = (
            harness.start_audio if case.media_type == "audio" else harness.start_video
        )
    else:
        operation = (
            harness.message.answer_audio
            if case.media_type == "audio"
            else harness.message.answer_video
        )
    operation.side_effect = RuntimeError("download or send failed")
    handler = import_module(f"handlers.button.{case.source}.download")
    with pytest.raises(RuntimeError, match="download or send failed"):
        await handler.download(harness.callback(case.payload(reuse_status)))
    cleanup = harness.exit_audio if case.media_type == "audio" else harness.exit_video
    cleanup.assert_awaited_once_with()
    status = harness.message if reuse_status else harness.status
    status.delete.assert_awaited_once_with()


async def test_youtube_metadata_failure_cleans_media_and_status(
    harness: DownloadHarness,
) -> None:
    harness.metadata.side_effect = ValueError("metadata unavailable")
    handler = import_module("handlers.button.youtube.download")
    with pytest.raises(ValueError, match="metadata unavailable"):
        await handler.download(harness.callback(VIDEO_CASES[0].payload()))
    harness.message.answer_video.assert_not_awaited()
    harness.exit_video.assert_awaited_once_with()
    harness.status.delete.assert_awaited_once_with()


@pytest.mark.parametrize(
    "case", CASES, ids=lambda case: f"{case.source}-{case.media_type}"
)
async def test_cancellation_cleans_media_and_status(
    case: DownloadCase, harness: DownloadHarness
) -> None:
    send = (
        harness.message.answer_audio
        if case.media_type == "audio"
        else harness.message.answer_video
    )
    send.side_effect = CancelledError()
    handler = import_module(f"handlers.button.{case.source}.download")
    with pytest.raises(CancelledError):
        await handler.download(harness.callback(case.payload()))
    cleanup = harness.exit_audio if case.media_type == "audio" else harness.exit_video
    cleanup.assert_awaited_once_with()
    harness.status.delete.assert_awaited_once_with()


async def test_porno365_resolve_failure_precedes_status(
    harness: DownloadHarness,
) -> None:
    harness.resolve_url.side_effect = ValueError("video unavailable")
    handler = import_module("handlers.button.porno365.download")
    with pytest.raises(ValueError, match="video unavailable"):
        await handler.download(harness.callback(VIDEO_CASES[3].payload()))
    harness.message.answer.assert_not_awaited()
    harness.start_video.assert_not_awaited()


@pytest.mark.parametrize(
    "identifier", ["https://vk.cc/abc123", "https://vk.com/video-123_456"]
)
@pytest.mark.parametrize("media_type", ["audio", "video"])
async def test_vk_full_url_compatibility(
    identifier: str, media_type: Literal["audio", "video"], harness: DownloadHarness
) -> None:
    case = DownloadCase("vk", "vkbtn", identifier, identifier, media_type)
    handler = import_module("handlers.button.vk.download")
    await handler.download(harness.callback(case.payload()))
    start = harness.start_audio if media_type == "audio" else harness.start_video
    start.assert_awaited_once_with(identifier)


@pytest.mark.parametrize("case", VIDEO_CASES, ids=lambda case: case.source)
async def test_router_registration(
    case: DownloadCase, harness: DownloadHarness
) -> None:
    handler = import_module(f"handlers.button.{case.source}.download")
    router = Router()
    handler.setup(router)
    registered = router.callback_query.handlers[0]
    assert registered.callback is handler.download
    assert (await registered.check(harness.callback(case.payload())))[0]
    assert not (await registered.check(harness.callback("unrelated:dlmp4:False:id")))[0]


@integration_test
@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "case",
    VIDEO_CASES[:2] + AUDIO_CASES,
    ids=lambda case: f"{case.source}-{case.media_type}",
)
async def test_download_integration(case: DownloadCase) -> None:
    """Keep the existing opt-in YouTube/VK Telegram smoke coverage."""
    handler = import_module(f"handlers.button.{case.source}.download")
    await handler.download(cast(CallbackQuery, CallbackEvent(case.payload())))


@pytest.mark.parametrize(
    "case", CASES, ids=lambda case: f"{case.source}-{case.media_type}"
)
@pytest.mark.parametrize("reuse_status", [False, True])
async def test_group_download_status_is_visible_only_to_callback_user(
    case: DownloadCase,
    reuse_status: bool,
    harness: DownloadHarness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = StatusHarness(monkeypatch)
    callback = transport.callback.model_copy(
        update={"data": case.payload(reuse_status), "message": transport.response(1)}
    )
    handler = import_module(f"handlers.button.{case.source}.download")
    await handler.download(callback)
    send, media, delete = transport.methods
    assert isinstance(send, SendMessage)
    assert send.ephemeral_message_parameters is not None
    assert send.ephemeral_message_parameters.receiver_user_id == transport.user.id
    assert send.ephemeral_message_parameters.callback_query_id == callback.id
    assert media.__api_method__ == (
        "sendAudio" if case.media_type == "audio" else "sendVideo"
    )
    assert isinstance(delete, DeleteEphemeralMessage)
    assert delete.receiver_user_id == transport.user.id
