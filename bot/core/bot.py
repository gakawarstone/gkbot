from collections.abc import Iterable

import uvloop
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.fsm.storage.memory import MemoryStorage

import handlers
import middlewares
import modules

from .default_commands import DefaultCommands
from .notifier import Notifier
from .types import BotConfig, StartupHook


async def run_startup_hooks(hooks: Iterable[StartupHook]) -> None:
    for hook in hooks:
        result = hook()
        if result is not None:
            await result


class BotStarter:
    __storage = MemoryStorage()

    def __init__(self, config: BotConfig):
        session = AiohttpSession(  # NOTE timeout
            api=TelegramAPIServer.from_base(config.api_url), timeout=300.0
        )
        self.bot = Bot(
            token=config.token,
            default=DefaultBotProperties(parse_mode=config.parse_mode),
            session=session,
        )
        self.dp = Dispatcher(storage=self.__storage, admins=config.admins)
        self.default_commands = config.default_commands
        self.startup_hooks = config.startup_hooks
        self.polling_tasks_concurrency_limit = config.polling_tasks_concurrency_limit

    async def __on_startup(self) -> None:
        await Notifier.setup(self.bot)
        await DefaultCommands(self.default_commands).set(self.bot)

        await run_startup_hooks(self.startup_hooks)

        middlewares.setup(self.dp)
        handlers.setup(self.dp)
        modules.setup(self.dp)
        await self.dp.start_polling(
            self.bot,
            tasks_concurrency_limit=self.polling_tasks_concurrency_limit,
        )

    def start(self) -> None:
        uvloop.run(self.__on_startup())
