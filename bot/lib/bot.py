import asyncio
from typing import Coroutine, Any

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage


class BotManager:
    __parse_mode = 'HTML'
    __storage = MemoryStorage()
    __loop = asyncio.get_event_loop()

    def __init__(self, token: str, api_url: str = 'https://api.telegram.org'):
        session = AiohttpSession(  # NOTE timeout
            api=TelegramAPIServer.from_base(api_url)
        )
        self.bot = Bot(
            token=token, parse_mode=self.__parse_mode, session=session)
        self.dp = Dispatcher(storage=self.__storage)
        self.__tasks_on_startup = []

    def add_tasks_on_startup(
            self, callbacks: list[Coroutine[Any, Any, Any]]
    ) -> None:
        self.__tasks_on_startup = callbacks

    async def __on_startup(self) -> None:
        for callback in self.__tasks_on_startup:
            await callback
        await self.dp.start_polling(self.bot)

    def start(self) -> None:
        self.__loop.run_until_complete(self.__on_startup())
