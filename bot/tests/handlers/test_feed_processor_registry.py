import asyncio
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SendPhoto
from aiogram.types import CallbackQuery, Message, URLInputFile

from modules.feed.handlers.messages import ShowFeedItemsHandler
from modules.feed.handlers.processors import FeedProcessor, FeedProcessorRegistry
from modules.feed.ui.keyboards import FeedMarkup
from services.gkfeed import FeedItem
from services.http import HttpRequestError


@pytest.fixture
def item() -> FeedItem:
    return FeedItem(
        id=11,
        feed_id=22,
        link="https://discours.io/articles/post",
        title="Feed title",
        text="Feed text",
    )


@pytest.fixture
def event(request: pytest.FixtureRequest) -> MagicMock:
    event_type = getattr(request, "param", Message)
    event = MagicMock(spec=event_type)
    event.from_user = MagicMock(id=7)
    event.answer_photo = AsyncMock()
    if event_type is CallbackQuery:
        event.message = MagicMock(spec=Message)
        event.message.answer_photo = event.answer_photo
    return event


@pytest.fixture
def bot() -> MagicMock:
    bot = MagicMock(spec=Bot)
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def handler(event: MagicMock, bot: MagicMock) -> ShowFeedItemsHandler:
    return ShowFeedItemsHandler(event=event, bot=bot)


@pytest.mark.parametrize("event", [Message, CallbackQuery], indirect=True)
async def test_discours_renders_photo_through_registry(
    handler: ShowFeedItemsHandler, item: FeedItem, event: MagicMock, bot: MagicMock
) -> None:
    with (
        patch(
            "modules.feed.handlers.processors.discours.HttpService.get_json",
            return_value={"data": {"title": "API title", "thumborId": "image-id"}},
        ) as get_json,
        patch(
            "services.open_graph.OpenGraphService.get",
            side_effect=AssertionError("unexpected generic extraction"),
        ),
    ):
        await handler._process_item(item)

    get_json.assert_awaited_once_with(
        "https://api.discours.io/api/v2/content-items/post"
    )
    photo = event.answer_photo.call_args.args[0]
    assert isinstance(photo, URLInputFile)
    assert photo.url == "https://assets.discours.io/unsafe/900x/image-id"
    event.answer_photo.assert_awaited_once()
    rendered = event.answer_photo.call_args.kwargs
    assert rendered["caption"] == f'<b>API title</b>\n\n<a href="{item.link}">Link</a>'
    assert rendered["reply_markup"] == FeedMarkup.get_item_markup(item.id, item.feed_id)
    bot.send_message.assert_not_awaited()


@pytest.mark.parametrize("event", [Message, CallbackQuery], indirect=True)
@pytest.mark.parametrize("failure", ["http", "photo"])
async def test_discours_failure_keeps_plain_link_fallback(
    handler: ShowFeedItemsHandler,
    item: FeedItem,
    failure: str,
    caplog: pytest.LogCaptureFixture,
    event: MagicMock,
    bot: MagicMock,
) -> None:
    if failure == "photo":
        event.answer_photo.side_effect = TelegramBadRequest(
            SendPhoto(chat_id=7, photo="image"), "invalid media"
        )
    with (
        patch(
            "modules.feed.handlers.processors.discours.HttpService.get_json",
            return_value={"data": {"title": "API title", "thumborId": "image-id"}},
            side_effect=HttpRequestError("private-payload")
            if failure == "http"
            else None,
        ),
        patch(
            "services.open_graph.OpenGraphService.get",
            side_effect=AssertionError("unexpected generic extraction"),
        ),
    ):
        await handler._process_item(item)

    bot.send_message.assert_awaited_once_with(
        7,
        f'<a href="{item.link}">discours</a>',
        reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
    )
    if failure == "http":
        event.answer_photo.assert_not_awaited()
        assert "processor=discours" in caplog.text
        assert "private-payload" not in caplog.text


@pytest.mark.parametrize("error", [KeyError("data"), asyncio.CancelledError()])
async def test_registry_processor_unexpected_error_propagates(
    handler: ShowFeedItemsHandler, item: FeedItem, error: BaseException, bot: MagicMock
) -> None:
    with (
        patch(
            "modules.feed.handlers.processors.discours.HttpService.get_json",
            side_effect=error,
        ),
        patch(
            "services.open_graph.OpenGraphService.get",
            side_effect=AssertionError("unexpected generic extraction"),
        ),
        pytest.raises(type(error)) as raised,
    ):
        await handler._process_item(item)
    assert raised.value is error
    bot.send_message.assert_not_awaited()


async def test_registry_fallback_failure_propagates_once(
    handler: ShowFeedItemsHandler, item: FeedItem, bot: MagicMock
) -> None:
    error = HttpRequestError("fallback failed")
    bot.send_message.side_effect = error
    with (
        patch(
            "modules.feed.handlers.processors.discours.HttpService.get_json",
            side_effect=HttpRequestError(),
        ),
        pytest.raises(HttpRequestError) as raised,
    ):
        await handler._process_item(item)
    assert raised.value is error
    bot.send_message.assert_awaited_once()


async def test_matching_failure_does_not_send_content_fallback(
    handler: ShowFeedItemsHandler, item: FeedItem, bot: MagicMock
) -> None:
    error = HttpRequestError("bad matcher")
    entry = FeedProcessor("broken", MagicMock(side_effect=error), AsyncMock())
    with (
        patch.object(
            type(handler),
            "_processor_registry",
            new_callable=PropertyMock,
            return_value=FeedProcessorRegistry((entry,)),
        ),
        pytest.raises(HttpRequestError) as raised,
    ):
        await handler._process_item(item)
    assert raised.value is error
    bot.send_message.assert_not_awaited()
