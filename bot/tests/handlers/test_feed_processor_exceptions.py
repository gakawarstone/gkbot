import asyncio
import traceback
from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramEntityTooLarge,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
    TelegramUnauthorizedError,
)
from aiogram.methods import SendPhoto
from aiogram.types import Message
from aiohttp import ClientConnectionError, ClientPayloadError, ClientResponseError
from bs4 import BeautifulSoup

from modules.feed.handlers._exceptions import FeedMediaExtractionError
from modules.feed.handlers.messages import ShowFeedItemsHandler
from services.gkfeed import FeedItem
from services.http import HttpRequestError
from services.matreshka import InvalidMatreshkaVideoUrl, MatreshkaVideoUnavailable
from services.tiktok.exceptions import (
    TikTokInfoExtractionFailed,
    TikTokInvalidUrl,
    TikTokVideoUrlExtractionFailed,
)
from services.youtube import UnavailableVideo

PHOTO_METHOD = SendPhoto(chat_id=1, photo="https://example.invalid/photo.jpg")


@pytest.fixture
def item() -> FeedItem:
    return FeedItem(
        id=11, feed_id=22, link="https://example.invalid", title="", text=""
    )


@pytest.fixture
def handler() -> ShowFeedItemsHandler:
    return ShowFeedItemsHandler(event=MagicMock(spec=Message))


@pytest.mark.parametrize(
    "error",
    [
        FeedMediaExtractionError("missing media"),
        HttpRequestError(),
        ClientConnectionError(),
        ClientPayloadError(),
        ClientResponseError(MagicMock(), (), status=503),
        TimeoutError(),
        InvalidMatreshkaVideoUrl("invalid"),
        MatreshkaVideoUnavailable("unavailable"),
        TikTokInfoExtractionFailed("unavailable"),
        TikTokInvalidUrl("invalid"),
        TikTokVideoUrlExtractionFailed("unavailable"),
        UnavailableVideo("unavailable"),
        TelegramBadRequest(PHOTO_METHOD, "invalid media"),
        TelegramEntityTooLarge(PHOTO_METHOD, "large media"),
        TelegramNetworkError(PHOTO_METHOD, "disconnected"),
        TelegramServerError(PHOTO_METHOD, "unavailable"),
    ],
    ids=lambda error: type(error).__name__,
)
async def test_recoverable_error_sends_plain_link(
    handler: ShowFeedItemsHandler, item: FeedItem, error: Exception
) -> None:
    with (
        patch.object(handler, "_process_base_item", new=AsyncMock(side_effect=error)),
        patch.object(handler, "_send_item", new_callable=AsyncMock) as send,
    ):
        await handler._process_item(item)
    send.assert_awaited_once_with(item)


@pytest.mark.parametrize(
    "error",
    [
        AttributeError("missing method"),
        TypeError("wrong arguments"),
        ValueError("wrong configuration"),
        KeyError("missing key"),
        IndexError("bad index"),
        RuntimeError("unexpected state"),
        TelegramForbiddenError(PHOTO_METHOD, "forbidden"),
        TelegramUnauthorizedError(PHOTO_METHOD, "invalid token"),
        TelegramRetryAfter(PHOTO_METHOD, "rate limit", retry_after=30),
        asyncio.CancelledError(),
    ],
    ids=lambda error: type(error).__name__,
)
async def test_unexpected_error_propagates_with_original_traceback(
    handler: ShowFeedItemsHandler, item: FeedItem, error: BaseException
) -> None:
    async def broken_processor(item: FeedItem) -> None:
        raise error

    with (
        patch.object(handler, "_process_base_item", new=broken_processor),
        patch.object(handler, "_send_item", new_callable=AsyncMock) as send,
        pytest.raises(type(error)) as raised,
    ):
        await handler._process_item(item)

    assert raised.value is error
    assert "broken_processor" in [
        frame.name for frame in traceback.extract_tb(raised.value.__traceback__)
    ]
    send.assert_not_awaited()


async def test_matched_processor_is_logged(
    handler: ShowFeedItemsHandler,
    item: FeedItem,
    caplog: pytest.LogCaptureFixture,
) -> None:
    item = replace(item, link="https://www.twitch.tv/channel")

    with (
        patch.object(
            handler, "_send_photo", new=AsyncMock(side_effect=HttpRequestError())
        ),
        patch.object(handler, "_process_base_item", new_callable=AsyncMock) as base,
        patch.object(handler, "_send_item", new_callable=AsyncMock) as send,
    ):
        await handler._process_item(item)

    send.assert_awaited_once_with(item)
    base.assert_not_awaited()
    assert "processor=twitch" in caplog.text


async def test_execution_accepts_bounded_registry_source_id(
    handler: ShowFeedItemsHandler,
    item: FeedItem,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with patch.object(handler, "_send_item", new_callable=AsyncMock):
        await handler._run_processor(
            item, AsyncMock(side_effect=HttpRequestError()), "discours" * 100
        )
    assert caplog.records[0].args == (item.id, item.feed_id, 0, ("discours" * 100)[:80])


async def test_success_does_not_send_fallback(
    handler: ShowFeedItemsHandler, item: FeedItem
) -> None:
    with (
        patch.object(handler, "_process_base_item", new_callable=AsyncMock) as process,
        patch.object(handler, "_send_item", new_callable=AsyncMock) as send,
    ):
        await handler._process_item(item)
    process.assert_awaited_once_with(item)
    send.assert_not_awaited()


@pytest.mark.parametrize("source", ["shiki", "vk", "instagram", "twitch"])
async def test_missing_external_content_uses_extraction_error(
    handler: ShowFeedItemsHandler, item: FeedItem, source: str
) -> None:
    links = {
        "shiki": "https://shikimori.one/animes/1",
        "vk": "https://vk.com/post",
        "instagram": "https://instagram.com/p/post",
        "twitch": "https://www.twitch.tv/",
    }
    item = replace(item, link=links[source])
    with (
        patch(
            "modules.feed.handlers.processors.shiki.get_html_soup",
            return_value=BeautifulSoup("", "html.parser"),
        ),
        patch("services.open_graph.HttpService.get", return_value=b""),
        patch.object(handler, "_send_item", new_callable=AsyncMock) as send,
    ):
        await handler._process_item(item)
    send.assert_awaited_once_with(item)


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
    handler: ShowFeedItemsHandler, item: FeedItem, title: str, image: str
) -> None:
    item = replace(
        item,
        link="https://instagram.com/p/post",
        title=title,
        text=f'<img src="{image}">',
    )
    with (
        patch.object(handler, "answer_photo", new_callable=AsyncMock) as photo,
        patch.object(handler, "_send_item", new_callable=AsyncMock) as send,
    ):
        await handler._process_item(item)
    photo.assert_not_awaited()
    send.assert_awaited_once_with(item)


async def test_shiki_missing_title_is_recoverable(
    handler: ShowFeedItemsHandler, item: FeedItem
) -> None:
    item = replace(item, link="https://shikimori.one/animes/1")
    soup = BeautifulSoup(
        '<meta property="og:image" content="image.jpg">', "html.parser"
    )
    with (
        patch(
            "modules.feed.handlers.processors.shiki.get_html_soup", return_value=soup
        ),
        patch.object(handler, "_send_item", new_callable=AsyncMock) as send,
    ):
        await handler._process_item(item)
    send.assert_awaited_once_with(item)


async def test_reddit_telegraph_programming_error_is_not_hidden(
    handler: ShowFeedItemsHandler, item: FeedItem
) -> None:
    item = replace(item, link="https://www.reddit.com/r/test/comments/post")
    soup = BeautifulSoup('<div class="post"></div>', "html.parser")
    error = AttributeError("missing telegraph method")
    with (
        patch(
            "services.open_graph.OpenGraphService.get", side_effect=HttpRequestError()
        ),
        patch("services.http.HttpService.get", return_value=str(soup).encode()),
        patch(
            "services.telegraph.TelegraphAPI.create_telegraph_page", side_effect=error
        ),
        patch.object(handler, "_send_item", new_callable=AsyncMock) as send,
        pytest.raises(AttributeError) as raised,
    ):
        await handler._process_item(item)
    assert raised.value is error
    send.assert_not_awaited()
