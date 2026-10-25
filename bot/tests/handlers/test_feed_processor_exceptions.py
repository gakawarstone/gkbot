import asyncio
import traceback
from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.methods import SendPhoto
from aiogram.types import Message, User

from modules.feed.handlers.messages import ShowFeedItemsHandler
from services.gkfeed import FeedItem
from services.http import HttpRequestError

PHOTO_METHOD = SendPhoto(chat_id=1, photo="https://example.invalid/photo.jpg")


@pytest.fixture
def item() -> FeedItem:
    return FeedItem(
        id=11, feed_id=22, link="https://example.invalid", title="", text=""
    )


@pytest.fixture
def bot() -> MagicMock:
    bot = MagicMock(spec=Bot)
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def handler(bot: MagicMock) -> ShowFeedItemsHandler:
    event = MagicMock(spec=Message)
    event.from_user = User(id=123, is_bot=False, first_name="Test")
    return ShowFeedItemsHandler(event=event, bot=bot)


@pytest.mark.parametrize(
    "error",
    [
        AttributeError("missing method"),
        TypeError("wrong arguments"),
        ValueError("wrong configuration"),
        TelegramForbiddenError(PHOTO_METHOD, "forbidden"),
        TelegramRetryAfter(PHOTO_METHOD, "rate limit", retry_after=30),
        asyncio.CancelledError(),
    ],
    ids=lambda error: type(error).__name__,
)
async def test_unexpected_error_propagates_with_original_traceback(
    handler: ShowFeedItemsHandler, item: FeedItem, error: BaseException, bot: MagicMock
) -> None:
    async def broken_processor(item: FeedItem) -> None:
        raise error

    with (
        patch.object(handler, "_process_base_item", new=broken_processor),
        pytest.raises(type(error)) as raised,
    ):
        await handler._process_item(item)

    assert raised.value is error
    assert "broken_processor" in [
        frame.name for frame in traceback.extract_tb(raised.value.__traceback__)
    ]
    bot.send_message.assert_not_awaited()


async def test_execution_accepts_bounded_registry_source_id(
    handler: ShowFeedItemsHandler,
    item: FeedItem,
    caplog: pytest.LogCaptureFixture,
) -> None:
    source_id = "discours" * 100
    await handler._run_processor(
        item, AsyncMock(side_effect=HttpRequestError()), source_id
    )
    message = caplog.records[0].getMessage()
    assert "discours" in message
    assert source_id not in message
    assert len(message) < 220


@pytest.mark.parametrize(
    ("title", "image"),
    [
        ("missing caption", "data:image/png;base64,AA=="),
        ("user:caption", "https://example.invalid/image.png"),
        ("user:caption", "data:image/png;base64"),
        ("user:caption", "data:image/png;base64,invalid!"),
        ("user:caption", "data:image/png;base64,\N{SNOWMAN}"),
    ],
)
async def test_malformed_instagram_media_falls_back(
    handler: ShowFeedItemsHandler,
    item: FeedItem,
    title: str,
    image: str,
    bot: MagicMock,
) -> None:
    item = replace(
        item,
        link="https://instagram.com/p/post",
        title=title,
        text=f'<img src="{image}">',
    )
    await handler._process_item(item)
    bot.send_message.assert_awaited_once()
    recipient, text = bot.send_message.await_args.args
    assert recipient == 123
    assert f'href="{item.link}"' in text


async def test_reddit_telegraph_programming_error_is_not_hidden(
    handler: ShowFeedItemsHandler, item: FeedItem, bot: MagicMock
) -> None:
    item = replace(item, link="https://www.reddit.com/r/test/comments/post")
    error = AttributeError("missing telegraph method")
    with (
        patch(
            "services.http.HttpService.get", return_value=b'<div class="post"></div>'
        ),
        patch(
            "services.telegraph.TelegraphAPI.create_telegraph_page", side_effect=error
        ),
        pytest.raises(AttributeError) as raised,
    ):
        await handler._process_item(item)
    assert raised.value is error
    bot.send_message.assert_not_awaited()
