from unittest.mock import MagicMock

import pytest
from aiogram.types import Message

from bot.filters.vk import VkVideoLink


@pytest.mark.asyncio
async def test_vk_video_link_filter():
    filter = VkVideoLink()

    # Valid vk.com links
    assert (
        await filter(
            MagicMock(spec=Message, text="https://vk.com/video-50883936_456244451")
        )
        is True
    )
    assert (
        await filter(
            MagicMock(spec=Message, text="https://vk.com/wall-50883936_456244451")
        )
        is True
    )
    assert await filter(MagicMock(spec=Message, text="https://vk.cc/abc-123")) is True

    # Valid vkvideo.ru link (the new one)
    assert (
        await filter(
            MagicMock(spec=Message, text="https://vkvideo.ru/video-50883936_456245496")
        )
        is True
    )

    # Invalid links
    assert await filter(MagicMock(spec=Message, text="https://google.com")) is False
    assert await filter(MagicMock(spec=Message, text="https://vk.com/other")) is False
