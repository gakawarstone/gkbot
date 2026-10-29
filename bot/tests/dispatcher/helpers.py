"""Offline transport and raw Telegram payloads for dispatcher integration tests."""

from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.fsm.context import FSMContext
from aiogram.methods import AnswerInlineQuery, DeleteMessage, SendDocument, SendMessage
from aiogram.methods.base import TelegramMethod, TelegramType
from aiogram.types import Chat, Message

from middlewares.data import UserData

USER_ID = 7001
ADMIN_IDS = [9001, 9002]


class RecordingSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[TelegramMethod[Any]] = []

    async def close(self) -> None:
        pass

    async def make_request(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: int | None = None,
    ) -> TelegramType:
        self.calls.append(method)
        result: Message | bool
        if isinstance(method, (SendMessage, SendDocument)):
            assert isinstance(method.chat_id, int)
            result = Message(
                message_id=1000 + len(self.calls),
                date=datetime(2026, 10, 23, tzinfo=UTC),
                chat=Chat(id=method.chat_id, type="private"),
                text=method.text if isinstance(method, SendMessage) else None,
            ).as_(bot)
        elif isinstance(method, (DeleteMessage, AnswerInlineQuery)):
            result = True
        else:
            pytest.fail(f"Unexpected Bot API method: {method.__api_method__}")
        # Aiogram's generic transport contract maps each method to its result type.
        return cast(TelegramType, result)

    async def stream_content(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes]:
        pytest.fail(f"Unexpected file download: {url}")
        yield b""  # pragma: no cover


@dataclass
class Invocation:
    state: FSMContext | None
    state_before: str | None
    user_data: UserData | None
    data_before: UserData | None


def raw_user(user_id: int = USER_ID) -> dict[str, Any]:
    return {
        "id": user_id,
        "is_bot": False,
        "first_name": "Dispatcher Test",
        "username": "dispatcher_test",
    }


def raw_message(
    text: str, *, user_id: int = USER_ID, message_id: int = 1
) -> dict[str, Any]:
    message: dict[str, Any] = {
        "message_id": message_id,
        "date": 1792756800,
        "chat": {"id": user_id, "type": "private"},
        "from": raw_user(user_id),
        "text": text,
    }
    if text.startswith("/"):
        message["entities"] = [
            {"type": "bot_command", "offset": 0, "length": len(text.split()[0])}
        ]
    return message


def callback_update(data: str, *, user_id: int = USER_ID) -> dict[str, Any]:
    return {
        "update_id": 2,
        "callback_query": {
            "id": "callback-2",
            "from": raw_user(user_id),
            "chat_instance": "offline-chat",
            "data": data,
            "message": raw_message("button message", user_id=user_id, message_id=42),
        },
    }


def inline_update(query: str) -> dict[str, Any]:
    return {
        "update_id": 3,
        "inline_query": {
            "id": "inline-3",
            "from": raw_user(),
            "query": query,
            "offset": "",
        },
    }


@dataclass
class DispatcherHarness:
    dispatcher: Dispatcher
    bot: Bot
    session: RecordingSession
    find_user: AsyncMock
    create_user: AsyncMock
    get_timezone: AsyncMock
    set_timezone: AsyncMock
    invocations: list[Invocation] = field(default_factory=list)

    async def message(self, text: str, *, user_id: int = USER_ID) -> Any:
        return await self.dispatcher.feed_raw_update(
            self.bot, {"update_id": 1, "message": raw_message(text, user_id=user_id)}
        )

    def state(self, user_id: int = USER_ID) -> FSMContext:
        return self.dispatcher.fsm.get_context(
            bot=self.bot, chat_id=user_id, user_id=user_id
        )
