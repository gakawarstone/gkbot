import asyncio
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from importlib import import_module
from io import BytesIO
from itertools import count
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.methods import (
    DeleteEphemeralMessage,
    EditMessageText,
    SendMessage,
)
from aiogram.types import InputMediaPhoto, URLInputFile

from handlers.text.instagram import InstagramPostDownloadHandler
from handlers.text.tiktok import TikTokVideoHandler
from handlers.text.ytdlp_short import YtdlpShortVideoHandler
from handlers.user.chatgpt.answer import AnswerHandler as ChatAnswerHandler
from handlers.user.cvision import AnswerHandler as VisionAnswerHandler
from services.agents.image_explainer import ImageExplainer
from services.instagram import InstagramService
from services.llm import OpenRouter
from services.llm.openrouter import StreamChunk
from services.matreshka import MatreshkaService
from services.sasflix import SasflixService
from services.tiktok import TikTokService
from services.ytdlp import YtdlpDownloader
from services.ytdlp._types import VideoFileInfo
from tests.mocks.status import StatusHarness


@pytest.mark.parametrize("source", ["tiktok", "instagram", "short"])
@pytest.mark.parametrize("failure", ["download", "cancel"])
async def test_text_download_uses_personal_status_and_cleans_failures(
    monkeypatch: pytest.MonkeyPatch, source: str, failure: str
) -> None:
    harness = StatusHarness(monkeypatch)
    video = VideoFileInfo(
        URLInputFile("https://example.invalid/video"), 720, 1280, 42, "Video"
    )

    async def fetch(*args: object) -> object:
        if failure == "download":
            raise OSError("download failed")
        if failure == "cancel":
            raise asyncio.CancelledError
        return video

    @asynccontextmanager
    async def download(url: str) -> AsyncIterator[VideoFileInfo]:
        await fetch(url)
        yield video

    if source == "tiktok":
        monkeypatch.setattr(TikTokService, "get_video", fetch)
        handler = TikTokVideoHandler(event=harness.message, bot=harness.bot)
    elif source == "instagram":

        async def photos(url: str) -> list[InputMediaPhoto]:
            await fetch(url)
            return [InputMediaPhoto(media="photo-file-id")]

        monkeypatch.setattr(InstagramService, "get_photos_album", photos)
        handler = InstagramPostDownloadHandler(event=harness.message, bot=harness.bot)
    else:
        monkeypatch.setattr(YtdlpDownloader, "download_video", download)
        handler = YtdlpShortVideoHandler(event=harness.message, bot=harness.bot)
    if failure == "download":
        with pytest.raises(OSError, match="download failed"):
            await handler.handle()
    elif failure == "cancel":
        with pytest.raises(asyncio.CancelledError):
            await handler.handle()
    sends = [method for method in harness.methods if isinstance(method, SendMessage)]
    assert len(sends) == 1
    assert sends[0].ephemeral_message_parameters is not None
    assert sends[0].ephemeral_message_parameters.receiver_user_id == harness.user.id
    assert isinstance(harness.methods[-1], DeleteEphemeralMessage)


@pytest.mark.parametrize("source", ["matreshka", "sasflix"])
async def test_additional_audio_callback_cleans_personal_status_on_failure(
    monkeypatch: pytest.MonkeyPatch, source: str
) -> None:
    harness = StatusHarness(monkeypatch)
    if source == "matreshka":
        service = MatreshkaService
        method = "get_video"
        payload = "matreshkabtn:123"
    else:
        service = SasflixService
        method = "get_audio"
        payload = "sasflixbtn:123"
    monkeypatch.setattr(
        service, method, AsyncMock(side_effect=OSError("download failed"))
    )
    callback = harness.callback.model_copy(update={"data": payload})
    handler = import_module(f"handlers.button.{source}.download")
    with pytest.raises(OSError, match="download failed"):
        await handler.download(callback)
    send, delete = harness.methods
    assert isinstance(send, SendMessage)
    assert send.ephemeral_message_parameters is not None
    assert send.ephemeral_message_parameters.callback_query_id == callback.id
    assert isinstance(delete, DeleteEphemeralMessage)


@pytest.mark.parametrize("source", ["chat", "vision"])
@pytest.mark.parametrize(
    "chat_type, failure",
    [("private", False), ("supergroup", False), ("supergroup", True)],
)
async def test_generation_wait_is_temporary_and_final_response_persists(
    monkeypatch: pytest.MonkeyPatch, source: str, chat_type: str, failure: bool
) -> None:
    harness = StatusHarness(monkeypatch, chat_type)

    async def chat_stream(*args: object) -> AsyncGenerator[StreamChunk]:
        if failure:
            raise OSError("generation failed")
        yield StreamChunk("An", "content")
        yield StreamChunk("swer", "content")

    async def vision_stream(*args: object) -> AsyncGenerator[str]:
        if failure:
            raise OSError("generation failed")
        yield "An"
        yield "swer"

    clock = count(step=2)
    module = import_module(
        "handlers.user.chatgpt.answer" if source == "chat" else "handlers.user.cvision"
    )
    monkeypatch.setattr(module, "time", SimpleNamespace(time=lambda: next(clock)))
    if source == "chat":
        monkeypatch.setattr(OpenRouter, "stream", chat_stream)
        handler = ChatAnswerHandler(
            event=harness.message, state=AsyncMock(), data={"messages": []}
        )
    else:
        monkeypatch.setattr(ImageExplainer, "explain", vision_stream)
        monkeypatch.setattr(
            VisionAnswerHandler, "_get_io", AsyncMock(return_value=BytesIO(b"image"))
        )
        message = harness.message.model_copy(
            update={"photo": [AsyncMock(file_id="photo")]}
        )
        handler = VisionAnswerHandler(event=message, state=AsyncMock())
    if failure:
        with pytest.raises(OSError, match="generation failed"):
            await handler.handle()
    else:
        await handler.handle()
    sends = [method for method in harness.methods if isinstance(method, SendMessage)]
    if chat_type == "supergroup":
        assert sends[0].ephemeral_message_parameters is not None
        assert any(
            isinstance(method, DeleteEphemeralMessage) for method in harness.methods
        )
        if not failure:
            assert len(sends) == 2
            final = harness.methods[-1]
            assert isinstance(final, EditMessageText)
            assert final.text == "Answer"
            assert sends[1].ephemeral_message_parameters is None
    elif not failure:
        assert len(sends) == 1
        final = harness.methods[-1]
        assert isinstance(final, EditMessageText)
        assert final.text == "Answer"
