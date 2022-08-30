import asyncio
from typing import Coroutine, Any

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message


class BotManager:
    __parse_mode = 'HTML'
    __storage = MemoryStorage()
    __loop = asyncio.get_event_loop()

    def __init__(self, token: str):
        self.bot = Bot(token=token, parse_mode=self.__parse_mode)
        self.dp = Dispatcher(storage=self.__storage)
        self.__tasks_on_startup = []

    def add_tasks_on_startup(
            self, callbacks: list[Coroutine[Any, Any, Any]]
    ) -> None:
        self.__tasks_on_startup = callbacks

    # FIXME delete
    async def send_message(self, id: int, text: str) -> Message:
        return await self.bot.send_message(id, text)

    async def on_startup(self) -> None:
        for callback in self.__tasks_on_startup:
            await callback
        await self.dp.start_polling(self.bot)

    def start(self) -> None:
        self.__loop.run_until_complete(self.on_startup())
