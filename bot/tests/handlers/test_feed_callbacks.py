import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, Message

from modules.feed.handlers.callbacks import ItemEventHandler
from services.gkfeed import FeedItem, GkfeedCredentials


class FeedCallbackHandler(ItemEventHandler):
    @property
    async def _gkfeed_credentials(self) -> GkfeedCredentials:
        return GkfeedCredentials(login="test", password="test")


def callback(action: str) -> CallbackQuery:
    return CallbackQuery.model_validate(
        {
            "id": "callback",
            "chat_instance": "chat",
            "from": {"id": 1234, "is_bot": False, "first_name": "User"},
            "data": f"fd:{action}:17",
            "message": {
                "message_id": 42,
                "date": 1_790_000_000,
                "chat": {"id": 1234, "type": "private"},
            },
        }
    )


@pytest.mark.parametrize("action", ["keep", "del"])
@pytest.mark.parametrize("has_next_item", [True, False])
async def test_item_actions_preserve_deletion_and_next_item_behavior(
    action: str, has_next_item: bool
) -> None:
    handler = FeedCallbackHandler(event=callback(action))
    item = FeedItem(
        id=18, feed_id=29, link="https://example.com", title="Next item", text=""
    )
    api = MagicMock()
    api.delete_item_by_id = AsyncMock()
    picker = MagicMock()
    picker.get_next_item = AsyncMock(return_value=item if has_next_item else None)

    with (
        patch("modules.feed.handlers.callbacks.GkfeedApi", return_value=api),
        patch("modules.feed.handlers.callbacks.GkfeedItemsPicker", return_value=picker),
        patch.object(Message, "delete", new_callable=AsyncMock) as delete_message,
        patch.object(handler, "_process_item", new_callable=AsyncMock) as process,
        patch.object(handler, "answer", new_callable=AsyncMock) as answer,
    ):
        await handler.handle()
        # Allow the existing background deletion task to complete within the mocks.
        await asyncio.sleep(0)

    delete_message.assert_awaited_once()
    if action == "del":
        api.delete_item_by_id.assert_awaited_once_with(17)
    else:
        api.delete_item_by_id.assert_not_called()
    picker.get_next_item.assert_awaited_once_with()
    if has_next_item:
        process.assert_awaited_once_with(item)
        answer.assert_not_awaited()
    else:
        process.assert_not_awaited()
        answer.assert_awaited_once_with("На данный момент ничего нового")


@pytest.mark.parametrize("action", ["show_all_feed", "unknown"])
async def test_obsolete_or_unknown_actions_do_not_change_the_feed(action: str) -> None:
    handler = FeedCallbackHandler(event=callback(action))

    with (
        patch("modules.feed.handlers.callbacks.GkfeedApi") as api,
        patch("modules.feed.handlers.callbacks.GkfeedItemsPicker") as picker,
        patch.object(Message, "delete", new_callable=AsyncMock) as delete_message,
        patch.object(handler, "_process_item", new_callable=AsyncMock) as process,
        patch.object(handler, "answer", new_callable=AsyncMock) as answer,
    ):
        await handler.handle()

    api.assert_not_called()
    picker.assert_not_called()
    delete_message.assert_not_awaited()
    process.assert_not_awaited()
    answer.assert_not_awaited()
