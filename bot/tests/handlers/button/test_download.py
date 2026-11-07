from asyncio import CancelledError
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, FSInputFile, Message

from handlers.button.porno365.download import download as download_porno365
from handlers.button.vk.download import download as download_vk
from handlers.button.youtube.download import download as download_youtube
from services.porno365 import Porno365Service
from services.youtube import YoutubeApiService
from services.ytdlp import YtdlpDownloader
from services.ytdlp._types import AudioFileInfo, VideoFileInfo

type FailureStage = Literal["download", "send", "cleanup"]


@dataclass
class DownloadState:
    callback: MagicMock
    visible_messages: set[str]
    media_path: Path
    metadata: AsyncMock
    resolve_url: AsyncMock
    failure: FailureStage | None = None
    error: BaseException | None = None

    def fail_at(self, stage: FailureStage) -> None:
        if self.failure == stage:
            assert self.error is not None
            raise self.error


@pytest.fixture
def state(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> DownloadState:
    message = MagicMock(spec=Message)
    status = MagicMock(spec=Message)
    callback = MagicMock(spec=CallbackQuery, message=message)
    state = DownloadState(
        callback=callback,
        visible_messages={"callback"},
        media_path=tmp_path / "downloaded-media",
        metadata=AsyncMock(),
        resolve_url=AsyncMock(),
    )

    async def create_status(text: str) -> MagicMock:
        state.visible_messages.add("status")
        return status

    async def delete_status() -> None:
        state.visible_messages.remove("status")

    async def delete_callback() -> None:
        state.visible_messages.remove("callback")

    async def send_media(*args: object, **kwargs: object) -> None:
        # Uploads must retain their downloaded file and progress message until done.
        assert state.media_path.is_file()
        assert state.visible_messages
        state.fail_at("send")

    message.answer = AsyncMock(side_effect=create_status)
    message.edit_text = AsyncMock()
    message.delete = AsyncMock(side_effect=delete_callback)
    status.delete = AsyncMock(side_effect=delete_status)
    message.answer_audio = AsyncMock(side_effect=send_media)
    message.answer_video = AsyncMock(side_effect=send_media)

    @asynccontextmanager
    async def media_file() -> AsyncIterator[FSInputFile]:
        state.media_path.write_bytes(b"downloaded media")
        try:
            state.fail_at("download")
            yield FSInputFile(state.media_path)
        finally:
            state.media_path.unlink()
            state.fail_at("cleanup")

    @asynccontextmanager
    async def download_audio(url: str) -> AsyncIterator[AudioFileInfo]:
        async with media_file() as file:
            yield AudioFileInfo(file, duration=123, title="Audio title")

    @asynccontextmanager
    async def download_video(url: str) -> AsyncIterator[VideoFileInfo]:
        async with media_file() as file:
            yield VideoFileInfo(
                file, height=720, width=1280, duration=456, title="Video title"
            )

    monkeypatch.setattr(YtdlpDownloader, "download_audio", download_audio)
    monkeypatch.setattr(YtdlpDownloader, "download_video", download_video)
    monkeypatch.setattr(YoutubeApiService, "get_video_data", state.metadata)
    monkeypatch.setattr(Porno365Service, "get_best_video_url", state.resolve_url)
    return state


@pytest.mark.parametrize("reuse_status", [False, True])
@pytest.mark.parametrize("failure", ["download", "send", "cleanup"])
async def test_failure_cleans_status(
    state: DownloadState, reuse_status: bool, failure: FailureStage
) -> None:
    state.callback.data = f"vkbtn:dlmp4:{reuse_status}:video-50883936_456244451"
    state.failure = failure
    state.error = RuntimeError("download lifecycle failure")

    with pytest.raises(RuntimeError) as raised:
        await download_vk(state.callback)

    assert raised.value is state.error
    assert state.visible_messages == (set() if reuse_status else {"callback"})
    assert not state.media_path.exists()


async def test_youtube_metadata_failure_cleans_download_and_status(
    state: DownloadState,
) -> None:
    state.callback.data = "ytbtn:dlmp4:False:oRxuDeZRFx8"
    error = ValueError("metadata unavailable")
    state.metadata.side_effect = error

    with pytest.raises(ValueError) as raised:
        await download_youtube(state.callback)

    assert raised.value is error
    assert state.visible_messages == {"callback"}
    assert not state.media_path.exists()


async def test_porno365_resolution_failure_precedes_status(
    state: DownloadState,
) -> None:
    state.callback.data = "p365btn:dlmp4:False:https://porno365.example/video/123"
    error = ValueError("video unavailable")
    state.resolve_url.side_effect = error

    with pytest.raises(ValueError) as raised:
        await download_porno365(state.callback)

    assert raised.value is error
    assert state.visible_messages == {"callback"}
    assert not state.media_path.exists()


@pytest.mark.parametrize("failure", ["download", "send"])
async def test_audio_failure_cleans_status(
    state: DownloadState, failure: FailureStage
) -> None:
    state.callback.data = "vkbtn:dlmp3:False:video-50883936_456244451"
    state.failure = failure
    state.error = RuntimeError("audio failure")

    with pytest.raises(RuntimeError) as raised:
        await download_vk(state.callback)

    assert raised.value is state.error
    assert state.visible_messages == {"callback"}
    assert not state.media_path.exists()


async def test_cancellation_cleans_download_and_status(state: DownloadState) -> None:
    state.callback.data = "vkbtn:dlmp4:False:video-50883936_456244451"
    state.failure = "send"
    state.error = CancelledError()

    with pytest.raises(CancelledError) as raised:
        await download_vk(state.callback)

    assert raised.value is state.error
    assert state.visible_messages == {"callback"}
    assert not state.media_path.exists()
