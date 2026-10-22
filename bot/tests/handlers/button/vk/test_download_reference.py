from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Message

from handlers.button.vk.download import download
from services.ytdlp import YtdlpDownloader


@pytest.mark.parametrize("action", ["dlmp3", "dlmp4"])
@pytest.mark.parametrize("use_status", [False, True])
@pytest.mark.parametrize(
    "value, expected_url",
    [
        ("wall-123_456", "https://vk.com/wall-123_456"),
        ("video-123_456", "https://vk.com/video-123_456"),
        ("https://vk.cc/abc-123", "https://vk.cc/abc-123"),
    ],
)
async def test_download_uses_reference_url(
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    use_status: bool,
    value: str,
    expected_url: str,
) -> None:
    downloaded_urls: list[str] = []

    @asynccontextmanager
    async def fake_download(url: str) -> AsyncIterator[SimpleNamespace]:
        downloaded_urls.append(url)
        yield SimpleNamespace(
            input_file="media", title="title", duration=1, width=2, height=3
        )

    method = "download_audio" if action == "dlmp3" else "download_video"
    monkeypatch.setattr(YtdlpDownloader, method, fake_download)
    status_message = MagicMock(spec=Message, delete=AsyncMock())
    message = MagicMock(
        spec=Message,
        answer=AsyncMock(return_value=status_message),
        edit_text=AsyncMock(),
        delete=AsyncMock(),
        answer_audio=AsyncMock(),
        answer_video=AsyncMock(),
    )
    callback = MagicMock(
        spec=CallbackQuery,
        message=message,
        data=f"vkbtn:{action}:{use_status}:{value}",
    )

    await download(callback)

    assert downloaded_urls == [expected_url]
    if action == "dlmp3":
        message.answer_audio.assert_awaited_once()
    else:
        message.answer_video.assert_awaited_once()
    if use_status:
        message.edit_text.assert_awaited_once_with("Cкачиваю " + expected_url)
        message.delete.assert_awaited_once()
    else:
        message.answer.assert_awaited_once_with("Cкачиваю " + expected_url)
        status_message.delete.assert_awaited_once()
