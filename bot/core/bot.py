import asyncio

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import middlewares
import handlers
from .types import BotConfig
from .notifier import Notifier
from .default_commands import DefaultCommands


class BotStarter:
    __storage = MemoryStorage()
    __loop = asyncio.get_event_loop()

    def __init__(self, config: BotConfig):
        session = AiohttpSession(  # NOTE timeout
            api=TelegramAPIServer.from_base(config.api_url)
        )
        self.bot = Bot(
            token=config.token, parse_mode=config.parse_mode, session=session
        )
        self.dp = Dispatcher(storage=self.__storage)
        self.default_commands = config.default_commands
        self.tasks_on_startup_async = config.tasks_on_startup_async
        self.tasks_on_startup_sync = config.tasks_on_startup_sync

    async def __on_startup(self) -> None:
        await Notifier.setup(self.bot)
        await DefaultCommands(self.default_commands).set(self.bot)

        for callback in self.tasks_on_startup_async:
            await callback

        for callback in self.tasks_on_startup_sync:
            callback()

        middlewares.setup(self.dp)
        handlers.setup(self.dp)
        await self.dp.start_polling(self.bot)

    def start(self) -> None:
        self.__loop.run_until_complete(self.__on_startup())
