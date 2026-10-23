from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Bot
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
)
from aiogram.methods import EditMessageMedia
from aiogram.types import (
    BufferedInputFile,
    Chat,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
    MessageEntity,
)

from handlers.text.instagram import InstagramPostDownloadHandler
from services.instagram import InstagramDownloadError, InstagramService

POST_URL = "https://www.instagram.com/p/test/"


@pytest.fixture(params=["photo", "video"])
def media(request: pytest.FixtureRequest) -> InputMediaPhoto | InputMediaVideo:
    if request.param == "photo":
        return InputMediaPhoto(
            media=BufferedInputFile(b"photo", filename="photo.jpg"),
            caption="<b>Photo</b>",
            parse_mode="HTML",
            show_caption_above_media=True,
            has_spoiler=True,
        )
    return InputMediaVideo(
        media=BufferedInputFile(b"video", filename="video.mp4"),
        thumbnail=BufferedInputFile(b"thumbnail", filename="thumbnail.jpg"),
        cover=BufferedInputFile(b"cover", filename="cover.jpg"),
        caption="Video",
        parse_mode=None,
        caption_entities=[MessageEntity(type="bold", offset=0, length=5)],
        show_caption_above_media=True,
        width=1920,
        height=1080,
        duration=12,
        start_timestamp=3,
        supports_streaming=True,
        has_spoiler=True,
    )


@dataclass
class HandlerContext:
    handler: InstagramPostDownloadHandler
    event: MagicMock
    status: MagicMock
    bot: AsyncMock


@pytest.fixture
def context() -> HandlerContext:
    status = MagicMock(spec=Message)
    status.edit_media = AsyncMock()
    status.edit_text = AsyncMock()
    status.delete = AsyncMock()
    event = MagicMock(spec=Message)
    event.text = POST_URL
    event.chat = Chat(id=123, type="private")
    event.delete = AsyncMock()
    event.answer = AsyncMock(return_value=status)
    event.answer_photo = AsyncMock()
    event.answer_video = AsyncMock()
    bot = AsyncMock(spec=Bot)
    return HandlerContext(
        InstagramPostDownloadHandler(event=event, bot=bot), event, status, bot
    )


async def test_single_media_reuses_status(
    context: HandlerContext,
    media: InputMediaPhoto | InputMediaVideo,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    download = AsyncMock(return_value=[media])
    monkeypatch.setattr(InstagramService, "get_photos_album", download)

    await context.handler.handle()

    download.assert_awaited_once_with(POST_URL)
    context.event.answer.assert_awaited_once_with(f"Скачиваю {POST_URL}")
    context.status.edit_media.assert_awaited_once_with(media)
    assert context.status.edit_media.await_args.args[0] is media
    context.status.delete.assert_not_awaited()
    context.event.answer_photo.assert_not_awaited()
    context.event.answer_video.assert_not_awaited()
    context.bot.send_media_group.assert_not_awaited()


@pytest.mark.parametrize(
    "error_type", [TelegramBadRequest, TelegramForbiddenError, TelegramNetworkError]
)
async def test_failed_edit_sends_media_and_cleans_status(
    context: HandlerContext,
    media: InputMediaPhoto | InputMediaVideo,
    monkeypatch: pytest.MonkeyPatch,
    error_type: type[TelegramAPIError],
) -> None:
    monkeypatch.setattr(
        InstagramService, "get_photos_album", AsyncMock(return_value=[media])
    )
    context.status.edit_media.side_effect = error_type(
        method=MagicMock(), message="Edit failed"
    )

    await context.handler.handle()

    send = (
        context.event.answer_video
        if isinstance(media, InputMediaVideo)
        else context.event.answer_photo
    )
    options = {
        name: getattr(media, name)
        for name in type(media).model_fields
        if name not in {"type", "media"}
    }
    send.assert_awaited_once_with(media.media, **options)
    context.status.delete.assert_awaited_once()
    context.bot.send_media_group.assert_not_awaited()


@pytest.mark.parametrize("count", [2, 10, 11, 21])
async def test_albums_keep_media_groups(
    context: HandlerContext,
    monkeypatch: pytest.MonkeyPatch,
    count: int,
) -> None:
    photos = [
        InputMediaPhoto(media=f"photo_{index}", caption=f"Photo {index}")
        for index in range(count)
    ]
    monkeypatch.setattr(
        InstagramService, "get_photos_album", AsyncMock(return_value=photos)
    )

    await context.handler.handle()

    context.status.edit_media.assert_not_awaited()
    groups = context.bot.send_media_group.await_args_list
    assert len(groups) == count // 10 + (count % 10 > 1)
    for index, call in enumerate(groups):
        assert call.args == (
            context.event.chat.id,
            photos[index * 10 : index * 10 + 10],
        )
    if count % 10 == 1:
        context.event.answer_photo.assert_awaited_once()
        call = context.event.answer_photo.await_args
        assert call.args == (photos[-1].media,)
        assert call.kwargs["caption"] == photos[-1].caption
    else:
        context.event.answer_photo.assert_not_awaited()
    context.status.delete.assert_awaited_once()


async def test_failed_cleanup_does_not_undo_delivery(
    context: HandlerContext,
    media: InputMediaPhoto | InputMediaVideo,
) -> None:
    error = TelegramBadRequest(method=MagicMock(), message="Message not found")
    context.status.edit_media.side_effect = error
    context.status.delete.side_effect = error

    await context.handler._send_media([media], context.status)

    context.status.delete.assert_awaited_once()


async def test_failed_fallback_preserves_status_and_raises(
    context: HandlerContext,
) -> None:
    error = TelegramBadRequest(method=MagicMock(), message="Upload failed")
    context.status.edit_media.side_effect = error
    context.event.answer_photo.side_effect = error

    with pytest.raises(TelegramBadRequest) as raised:
        await context.handler._send_media(
            [InputMediaPhoto(media="photo")], context.status
        )

    assert raised.value is error
    context.status.delete.assert_not_awaited()


async def test_download_failure_keeps_error_status(
    context: HandlerContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        InstagramService,
        "get_photos_album",
        AsyncMock(side_effect=InstagramDownloadError(POST_URL)),
    )

    await context.handler.handle()

    context.status.edit_text.assert_awaited_once_with(
        f"Не получилось скачать {POST_URL}"
    )
    context.status.edit_media.assert_not_awaited()
    context.status.delete.assert_not_awaited()


async def test_edit_targets_existing_status_message(
    context: HandlerContext,
    media: InputMediaPhoto | InputMediaVideo,
) -> None:
    bot = Bot(token="12345678:ABCDEF-GHIJKLMNOPQRSTUV")
    status = Message(
        message_id=456,
        date=datetime.now(UTC),
        chat=Chat(id=123, type="private"),
        text="Downloading",
    ).as_(bot)
    async with bot:
        request = AsyncMock(return_value=status)
        with patch.object(bot.session, "make_request", new=request):
            await context.handler._send_media([media], status)

        assert request.await_args is not None
        method = request.await_args.args[1]
        assert isinstance(method, EditMessageMedia)
        assert method.chat_id == status.chat.id
        assert method.message_id == status.message_id
        assert method.media is media
        assert request.await_count == 1
