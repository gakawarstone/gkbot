from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.methods import SendVideo
from aiogram.types import BufferedInputFile, Message

from services.video import VideoMetadata
from ui.video import send_video


async def test_rejected_metadata_retries_original_arguments() -> None:
    file = BufferedInputFile(b"video", "video.mp4")
    thumbnail = BufferedInputFile(b"thumbnail", "thumbnail.jpg")
    method = SendVideo(chat_id=123, video=file)
    error = TelegramBadRequest(method, "Bad Request: failed to get HTTP URL content")
    message = MagicMock(spec=Message)
    sender = AsyncMock(side_effect=[error, message])
    metadata = VideoMetadata(cover="https://example.com/cover.jpg", start_timestamp=12)
    kwargs = {
        "caption": "caption",
        "duration": 60,
        "thumbnail": thumbnail,
        "has_spoiler": True,
    }
    assert await send_video(sender, file, metadata=metadata, **kwargs) is message
    assert sender.await_count == 2
    assert sender.await_args_list[0].kwargs == dict(
        kwargs, cover=metadata.cover, start_timestamp=12
    )
    assert sender.await_args_list[1].args == (file,)
    assert sender.await_args_list[1].kwargs == kwargs


@pytest.mark.parametrize("network_error", [False, True])
async def test_send_errors_are_not_retried_without_metadata_or_on_network_failure(
    network_error: bool,
) -> None:
    method = SendVideo(chat_id=123, video="video-id")
    error_type = TelegramNetworkError if network_error else TelegramBadRequest
    error = error_type(method, "send failed")
    sender = AsyncMock(side_effect=error)
    metadata = (
        VideoMetadata(cover="https://example.com/cover.jpg") if network_error else None
    )
    with pytest.raises(error_type) as raised:
        await send_video(sender, "video-id", metadata=metadata)
    assert raised.value is error
    sender.assert_awaited_once()


async def test_retry_is_bounded_and_invalid_metadata_is_omitted() -> None:
    method = SendVideo(chat_id=123, video="video-id")
    error = TelegramBadRequest(method, "send failed")
    sender = AsyncMock(side_effect=error)
    with pytest.raises(TelegramBadRequest):
        await send_video(sender, "video-id", metadata=VideoMetadata(start_timestamp=12))
    assert sender.await_count == 2
    sender.reset_mock()
    sender.side_effect = None
    await send_video(
        sender,
        "video-id",
        metadata=VideoMetadata(cover="file:///tmp/cover.jpg", start_timestamp=-1),
    )
    sender.assert_awaited_once_with("video-id")
