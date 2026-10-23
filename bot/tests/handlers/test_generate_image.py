from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import BufferedInputFile, InputMediaPhoto, Message

from handlers.prompt.generate_image import generate_image
from services.agents.image_prompt_enhancer import ImagePromptEnhancer
from services.http import HttpService


async def test_generated_album_contains_downloaded_photos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    message = MagicMock(
        spec=Message,
        text="/img a cat",
        delete=AsyncMock(),
        answer_media_group=AsyncMock(),
    )
    enhance = AsyncMock(return_value="enhanced cat")
    download = AsyncMock(side_effect=[b"one", b"two", b"three", b"four"])
    monkeypatch.setattr(ImagePromptEnhancer, "enhance", enhance)
    monkeypatch.setattr(HttpService, "get", download)

    await generate_image(message)

    message.delete.assert_awaited_once_with()
    enhance.assert_awaited_once_with("a cat")
    message.answer_media_group.assert_awaited_once()
    media = message.answer_media_group.call_args.args[0]
    assert len(media) == 4
    for photo, expected in zip(media, [b"one", b"two", b"three", b"four"], strict=True):
        assert isinstance(photo, InputMediaPhoto)
        assert isinstance(photo.media, BufferedInputFile)
        assert photo.media.data == expected
    assert download.await_count == 4
    assert all("enhanced+cat" in call.args[0] for call in download.call_args_list)
