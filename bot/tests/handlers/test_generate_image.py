from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import InputFile, InputMediaPhoto, Message

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
    expected = [b"one", b"two", b"three", b"four"]
    download = AsyncMock(side_effect=expected)
    monkeypatch.setattr(ImagePromptEnhancer, "enhance", enhance)
    monkeypatch.setattr(HttpService, "get", download)

    await generate_image(message)

    media = message.answer_media_group.call_args.args[0]
    delivered = []
    for photo in media:
        assert isinstance(photo, InputMediaPhoto)
        assert isinstance(photo.media, InputFile)
        delivered.append(
            b"".join([chunk async for chunk in photo.media.read(MagicMock())])
        )
    assert sorted(delivered) == sorted(expected)
