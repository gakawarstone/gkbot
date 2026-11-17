from functools import partial
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from aiogram.types import Message

from configs.admins import ADMINS

from .. import INTEGRATION_TEST

if INTEGRATION_TEST:
    from aiogram import Bot as _AiogramBot
    from aiogram.client.default import DefaultBotProperties
    from aiogram.client.session.aiohttp import AiohttpSession
    from aiogram.client.telegram import TelegramAPIServer

    from configs.env import API_SERVER_URL, BOT_TOKEN

    if BOT_TOKEN is None:
        raise ValueError("BOT_TOKEN is required for integration tests")
    if API_SERVER_URL is None:
        raise ValueError("API_SERVER_URL is required for integration tests")

    bot = _AiogramBot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
        session=AiohttpSession(api=TelegramAPIServer.from_base(API_SERVER_URL)),
    )


def make_sent_message() -> MagicMock:
    return MagicMock(spec=Message, delete=AsyncMock(), edit_text=AsyncMock())


class Bot:
    def __init__(self) -> None:
        self.send_message = AsyncMock(side_effect=partial(self._send, "send_message"))
        self.send_video = AsyncMock(side_effect=partial(self._send, "send_video"))
        self.send_photo = AsyncMock(side_effect=partial(self._send, "send_photo"))
        self.send_audio = AsyncMock(side_effect=partial(self._send, "send_audio"))
        self.send_chat_action = AsyncMock(return_value=True)
        if INTEGRATION_TEST:
            self.send_chat_action.side_effect = bot.send_chat_action

    async def _send(self, method: str, *args: Any, **kwargs: Any) -> Any:
        if INTEGRATION_TEST:
            message = await getattr(bot, method)(*args, **kwargs)
            # Keep integration chats clean without an interactive debugger.
            if method != "send_message":
                await message.delete()
            return message
        return make_sent_message()


class _FromUser:
    id = ADMINS[0]
    username = "admin"


class _Chat:
    id = ADMINS[0]


class Event:
    from_user = _FromUser()
    chat = _Chat()

    def __init__(self, text: str | None = None) -> None:
        self.text = text
        self.bot = Bot()
        self.delete = AsyncMock()
        self.answer = AsyncMock(side_effect=partial(self.bot.send_message, ADMINS[0]))
        self.answer_photo = AsyncMock(
            side_effect=partial(self.bot.send_photo, ADMINS[0])
        )
        self.answer_audio = AsyncMock(
            side_effect=partial(self.bot.send_audio, ADMINS[0])
        )
        self.answer_video = AsyncMock(
            side_effect=partial(self.bot.send_video, ADMINS[0])
        )


class CallbackEvent(Event):
    def __init__(self, callback_data: str) -> None:
        super().__init__()
        self.data = callback_data
        self.message = Event()
