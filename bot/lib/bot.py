from typing import Awaitable
import logging

import aiogram
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, Message, ParseMode,
                           ReplyKeyboardMarkup)


class Bot(object):
    def __init__(self, token: str):
        self.__bot = self.__set_bot(token)
        self.dp = self.__set_dispatcher(self.__bot)
        self.admins = []
        self.keyboards = {}
        self.inline_keyboards = {}
        self.tasks = []

    def __set_bot(self, token: str,
                  parse_mode: ParseMode = ParseMode.HTML) -> aiogram.Bot:
        return aiogram.Bot(token=token, parse_mode=parse_mode)

    def __set_dispatcher(self, bot: aiogram.Bot) -> Dispatcher:
        storage = MemoryStorage()
        return Dispatcher(bot, storage=storage)

    def get_bot_instance(self) -> aiogram.Bot:
        return self.__bot

    def add_message_handler(self, func: Awaitable[Message]) -> None:
        @self.dp.message_handler()
        async def handler(message: Message):
            await func(message)

    def add_command_handler(self, command: str, func: Awaitable[Message],
                            admin_only: bool = False) -> None:
        ''' command - /<command> in telegram '''
        @self.dp.message_handler(commands=[command])
        async def handler(message: Message):
            is_admin = message['from']['id'] in self.admins
            if not admin_only or admin_only and is_admin:
                await func(message)
        logging.debug('Command handler added at command /' + command)

    def add_state_handler(self, state: FSMContext,
                          func: Awaitable[Message]) -> None:
        @self.dp.message_handler(state=state)
        async def handler(message: Message, state: FSMContext):
            await func(message, state)

    def add_channel_post_handler(self, func: Awaitable[Message]) -> None:
        @self.dp.channel_post_handler()
        async def handler(message: Message):
            await func(message)

    def add_keyboard(self, name: str, buttons: list[list[str]],
                     hide: bool = True, placeholder: str = None) -> None:
        ''' add telegram keyboard with row of {buttons}
            call by {bot_object.keyboards[name]} '''
        kb = ReplyKeyboardMarkup(resize_keyboard=True,
                                 one_time_keyboard=hide,
                                 input_field_placeholder=placeholder)
        for rows in buttons:
            kb.row(*(KeyboardButton(i) for i in rows))
        self.keyboards[name] = kb

    def add_url_button(self, url: str,
                       text: str = 'request') -> InlineKeyboardMarkup:
        btn = InlineKeyboardButton(text, url=url)
        self.inline_keyboards[url] = InlineKeyboardMarkup().add(btn)
        return self.inline_keyboards[url]

    def add_on_startup(self, func: Awaitable) -> None:
        self.tasks.append(func)

    async def send_message(self, id: int, text: str) -> Message:
        return await self.__bot.send_message(id, text)

    async def send_file(self, message: str, path: str) -> None:
        await message.answer_document(open(path, "rb"))

    async def on_startup(self, dp: Dispatcher) -> None:
        for func in self.tasks:
            await func(dp)

    def start(self) -> None:
        executor = aiogram.utils.executor
        if self.tasks:
            executor.start_polling(self.dp, on_startup=self.on_startup)
        else:
            executor.start_polling(self.dp)
