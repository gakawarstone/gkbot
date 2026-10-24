from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Chat, InputMediaPhoto, Message

from handlers.text.instagram import InstagramPostDownloadHandler
from services.instagram import InstagramService

POST_URL = "https://www.instagram.com/p/test/"


@dataclass
class HandlerContext:
    handler: InstagramPostDownloadHandler
    event: MagicMock
    status: MagicMock


@pytest.fixture
def context() -> HandlerContext:
    status = MagicMock(spec=Message)
    status.edit_media = AsyncMock()
    status.delete = AsyncMock()
    event = MagicMock(spec=Message)
    event.text = POST_URL
    event.chat = Chat(id=123, type="private")
    event.delete = AsyncMock()
    event.answer = AsyncMock(return_value=status)
    event.answer_photo = AsyncMock()
    handler = InstagramPostDownloadHandler(event=event, bot=AsyncMock(spec=Bot))
    return HandlerContext(handler, event, status)


async def test_failed_cleanup_does_not_undo_delivery(
    context: HandlerContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        InstagramService,
        "get_photos_album",
        AsyncMock(return_value=[InputMediaPhoto(media="photo")]),
    )
    error = TelegramBadRequest(method=MagicMock(), message="Message not found")
    context.status.edit_media.side_effect = error
    context.status.delete.side_effect = error

    await context.handler.handle()

    context.status.delete.assert_awaited_once()


async def test_failed_fallback_preserves_status_and_raises(
    context: HandlerContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        InstagramService,
        "get_photos_album",
        AsyncMock(return_value=[InputMediaPhoto(media="photo")]),
    )
    error = TelegramBadRequest(method=MagicMock(), message="Upload failed")
    context.status.edit_media.side_effect = error
    context.event.answer_photo.side_effect = error

    with pytest.raises(TelegramBadRequest) as raised:
        await context.handler.handle()

    assert raised.value is error
    context.status.delete.assert_not_awaited()
