import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest
from aiogram.types import CallbackQuery, Message

from modules.feed.handlers.callbacks import ItemEventHandler
from services.gkfeed import FeedItem, GkfeedCredentials
from services.gkfeed.api import GkfeedApi


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


async def test_obsolete_similar_callback_does_not_change_the_feed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event = callback("show_all_feed")
    assert isinstance(event.message, Message)
    original_message = event.message
    chat_messages = {original_message.message_id: "Current feed item"}
    saved_items = {17}
    unread_items: list[FeedItem] = []

    async def get_user_items(api: GkfeedApi) -> AsyncIterator[FeedItem]:
        for item in unread_items:
            yield item

    async def delete_item(api: GkfeedApi, item_id: int) -> None:
        saved_items.discard(item_id)

    async def delete_message(message: Message) -> bool:
        chat_messages.pop(message.message_id, None)
        return True

    async def send_reply(message: Message, text: str, **kwargs: Any) -> Message:
        chat_messages[max(chat_messages, default=0) + 1] = text
        return original_message

    monkeypatch.setattr(GkfeedApi, "get_user_items", get_user_items)
    monkeypatch.setattr(GkfeedApi, "delete_item_by_id", delete_item)
    monkeypatch.setattr(Message, "delete", delete_message)
    monkeypatch.setattr(Message, "answer", send_reply)

    await FeedCallbackHandler(event=event).handle()
    await asyncio.sleep(0)

    assert chat_messages == {original_message.message_id: "Current feed item"}
    assert saved_items == {17}
