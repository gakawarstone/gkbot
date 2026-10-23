from typing import cast
from unittest.mock import AsyncMock

import pytest
from aiogram.types import BufferedInputFile, Message

from handlers.text.tiktok import TikTokVideoHandler
from services.tiktok import TikTokService
from services.tiktok.exceptions import TikTokInfoExtractionFailed, TikTokInvalidUrl
from services.tiktok.types import TikTokVideo
from tests.handlers import Event, make_sent_message


@pytest.mark.parametrize(
    "failure", [None, TikTokInvalidUrl, TikTokInfoExtractionFailed]
)
async def test_tiktok_handler_records_delivery_and_failure(
    monkeypatch: pytest.MonkeyPatch, failure: type[Exception] | None
) -> None:
    url = "https://example.invalid/tiktok"
    event = Event(url)
    input_file = BufferedInputFile(b"video", "video.mp4")
    video = TikTokVideo(
        url=None, input_file=input_file, height=720, width=1080, duration=12
    )
    status = make_sent_message()
    event.answer.side_effect = None
    event.answer.return_value = status
    get_video = AsyncMock(return_value=video)
    if failure is not None:
        get_video.side_effect = failure(url)
    monkeypatch.setattr(TikTokService, "get_video", get_video)

    await TikTokVideoHandler(event=cast(Message, event), bot=event.bot).handle()

    event.delete.assert_awaited_once_with()
    event.answer.assert_awaited_once_with(f"Скачиваю {url}")
    event.bot.send_chat_action.assert_awaited_once_with(event.chat.id, "upload_video")
    get_video.assert_awaited_once_with(url)
    if failure is None:
        event.answer_video.assert_awaited_once_with(
            input_file,
            caption=f'<b>admin</b> ➤ <a href="{url}">TikTok</a>',
            height=720,
            width=1080,
            duration=12,
        )
        status.delete.assert_awaited_once_with()
        status.edit_text.assert_not_awaited()
    else:
        event.answer_video.assert_not_awaited()
        status.delete.assert_not_awaited()
        prefix = (
            "Неправильная ссылка"
            if failure is TikTokInvalidUrl
            else "Не получилось скачать"
        )
        status.edit_text.assert_awaited_once_with(f"{prefix} {url}")


async def test_offline_messages_can_be_checked_and_do_not_share_calls() -> None:
    first = Event("first")
    second = Event("second")
    message = await first.answer("working")
    await message.edit_text("done")
    await message.delete()

    first.answer.assert_awaited_once_with("working")
    first.bot.send_message.assert_awaited_once_with(first.chat.id, "working")
    message.edit_text.assert_awaited_once_with("done")
    message.delete.assert_awaited_once_with()
    second.answer.assert_not_awaited()
    second.bot.send_message.assert_not_awaited()
