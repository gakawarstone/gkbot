from typing import Optional

from configs.admins import ADMINS
from .. import INTEGRATION_TEST

BREAKPOINTS_ON_DELETE = 1


if INTEGRATION_TEST:
    from aiogram import Bot as _AiogramBot
    from aiogram.client.session.aiohttp import AiohttpSession
    from aiogram.client.telegram import TelegramAPIServer
    from aiogram.client.default import DefaultBotProperties
    from configs.env import BOT_TOKEN, API_SERVER_URL

    # Ensure BOT_TOKEN and API_SERVER_URL are not None for integration tests
    if BOT_TOKEN is None:
        raise ValueError("BOT_TOKEN is required for integration tests")

    if API_SERVER_URL is None:
        raise ValueError("API_SERVER_URL is required for integration tests")

    bot = _AiogramBot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
        session=AiohttpSession(api=TelegramAPIServer.from_base(API_SERVER_URL)),
    )


class Bot:
    _messages: list = []

    async def send_message(self, *args, **kwargs):
        if INTEGRATION_TEST:
            m = await bot.send_message(*args, **kwargs)
            if BREAKPOINTS_ON_DELETE:
                breakpoint()
            await m.delete()

    async def send_video(self, *args, **kwargs):
        if INTEGRATION_TEST:
            m = await bot.send_video(*args, **kwargs)
            if BREAKPOINTS_ON_DELETE:
                breakpoint()
            await m.delete()

    async def send_photo(self, *args, **kwargs):
        if INTEGRATION_TEST:
            m = await bot.send_photo(*args, **kwargs)
            if BREAKPOINTS_ON_DELETE:
                breakpoint()
            await m.delete()

    async def send_chat_action(self, *args, **kwargs):
        if INTEGRATION_TEST:
            if not await bot.send_chat_action(*args, **kwargs):
                raise ValueError("failed to send action")


class _FromUser:
    id = ADMINS[0]
    username = "admin"


class _Chat:
    id = ADMINS[0]


class Event:
    from_user = _FromUser()
    chat = _Chat()

    def __init__(
        self,
        text: Optional[str] = None,
        breakpoint_at_delete: bool = bool(BREAKPOINTS_ON_DELETE),
    ) -> None:
        self.text = text
        self._breakpoint_at_delete = breakpoint_at_delete

    async def delete(self):
        if self._breakpoint_at_delete:
            breakpoint()

    async def answer_photo(self, *args, **kwargs):
        if INTEGRATION_TEST:
            _args = list(args)
            _args.insert(0, ADMINS[0])
            m = await bot.send_photo(*_args, **kwargs)
            if BREAKPOINTS_ON_DELETE:
                breakpoint()
            return await m.delete()

    async def answer_audio(self, *args, **kwargs):
        if INTEGRATION_TEST:
            _args = list(args)
            _args.insert(0, ADMINS[0])
            m = await bot.send_audio(*_args, **kwargs)
            if BREAKPOINTS_ON_DELETE:
                breakpoint()
            return await m.delete()

    async def answer_video(self, *args, **kwargs):
        if INTEGRATION_TEST:
            _args = list(args)
            _args.insert(0, ADMINS[0])
            m = await bot.send_video(*_args, **kwargs)
            if BREAKPOINTS_ON_DELETE:
                breakpoint()
            return await m.delete()

    async def answer(self, *args, **kwargs):
        if INTEGRATION_TEST:
            _args = list(args)
            _args.insert(0, ADMINS[0])
            return await bot.send_message(*_args, **kwargs)
            # await m.delete()


class CallbackEvent(Event):
    def __init__(
        self,
        callback_data: str,
        breakpoint_at_delete: bool = bool(BREAKPOINTS_ON_DELETE),
    ) -> None:
        self.data = callback_data
        self.message = Event()
        super().__init__(breakpoint_at_delete=breakpoint_at_delete)
