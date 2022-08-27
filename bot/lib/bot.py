import asyncio
import logging
from typing import Awaitable

import aiogram
from aiogram import Dispatcher
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder


class BotManager:
    def __init__(self, token: str):
        self.bot = self.__set_bot(token)
        self.dp = self.__set_dispatcher()
        self.inline_keyboards = {}
        self.__tasks = []

    def __set_bot(self, token: str, parse_mode: str = 'HTML') -> aiogram.Bot:
        return aiogram.Bot(token=token, parse_mode=parse_mode)

    def __set_dispatcher(self) -> Dispatcher:  # [ ] storage not only one
        return Dispatcher(storage=MemoryStorage())

    def add_message_handler(self, func: Awaitable[Message]) -> None:
        self.dp.register_message(func)

    def add_command_handler(self, command: str,
                            func: Awaitable[Message]) -> None:
        ''' command - /<command> in telegram '''
        self.dp.register_message(func, commands=[command])

        logging.debug('Command handler added at command /' + command)

    def add_state_handler(self, state: FSMContext,
                          func: Awaitable[Message]) -> None:
        self.dp.register_message(
            func, state=state, content_types=['text'])

    def add_channel_post_handler(self, func: Awaitable[Message]) -> None:
        @self.dp.channel_post_handler()
        async def handler(message: Message):
            await func(message)

    def add_url_button(self, url: str,
                       text: str = 'request') -> InlineKeyboardMarkup:
        btn = InlineKeyboardButton(text=text, url=url)
        self.inline_keyboards[url] = InlineKeyboardBuilder().add(
            btn).as_markup()
        return self.inline_keyboards[url]

    def add_tasks_on_startup(self, functions: list[Awaitable]) -> None:
        self.__tasks = functions

    async def send_message(self, id: int, text: str) -> Message:
        return await self.bot.send_message(id, text)

    async def on_startup(self) -> None:
        for func in self.__tasks:
            await func()

    def start(self) -> None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.on_startup())
        loop.run_until_complete(self.dp.start_polling(self.bot))
