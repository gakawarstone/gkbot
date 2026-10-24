"""An aiogram transport double for status and handler contract tests."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.methods import SendMessage, TelegramMethod
from aiogram.types import CallbackQuery, Chat, Message, User


class StatusHarness:
    def __init__(
        self, monkeypatch: pytest.MonkeyPatch, chat_type: str = "supergroup"
    ) -> None:
        self.bot = Bot("12345678:ABCDEF-GHIJKLMNOPQRSTUV")
        self.chat = Chat(id=-42 if chat_type != "private" else 42, type=chat_type)
        self.user = User(id=7, is_bot=False, first_name="Requester")
        self.supported = True
        self.send_error: TelegramAPIError | None = None
        self.cleanup_error: TelegramAPIError | None = None
        self.request = AsyncMock(side_effect=self._respond)
        monkeypatch.setattr(self.bot.session, "make_request", self.request)
        self.message = self.response(1).model_copy(
            update={"from_user": self.user, "text": "https://example.invalid/video"}
        )
        self.callback = CallbackQuery(
            id="callback-7",
            from_user=self.user,
            chat_instance="group",
            data="download",
            message=self.message,
        ).as_(self.bot)

    def response(self, message_id: int, ephemeral: bool = False) -> Message:
        return Message(
            message_id=0 if ephemeral else message_id,
            date=datetime.fromtimestamp(1, UTC),
            chat=self.chat,
            from_user=User(id=self.bot.id, is_bot=True, first_name="Bot"),
            ephemeral_message_id=91 if ephemeral else None,
            receiver_user=self.user if ephemeral else None,
        ).as_(self.bot)

    async def _respond(
        self, bot: Bot, method: TelegramMethod[object], timeout: int | None = None
    ) -> Message | bool:
        if method.__api_method__.startswith("delete") and self.cleanup_error:
            raise self.cleanup_error
        if isinstance(method, SendMessage):
            if method.ephemeral_message_parameters is not None and self.send_error:
                raise self.send_error
            return self.response(
                2,
                ephemeral=self.supported
                and method.ephemeral_message_parameters is not None,
            )
        return True

    @property
    def methods(self) -> list[TelegramMethod[object]]:
        return [call.args[1] for call in self.request.await_args_list]
