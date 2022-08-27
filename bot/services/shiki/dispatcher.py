import asyncio
from typing_extensions import Self

from aiogram import Dispatcher, Bot

from .user_updates import User, Update, UserUpdates


class _UserUpdatesSubscription:
    def __init__(self, chat_id: int, shiki_name: str) -> None:
        self.chat_id = chat_id
        self.user = User(shiki_name)
        self.user_updates = UserUpdates(self.user)

    async def setup(self):
        self.last_update = await self.__get_last_update()
        return self

    async def __get_last_update(self) -> Update:
        updates = await self.user_updates.load_latest(1)
        return updates[0]

    async def is_updated(self) -> bool:
        new_update = await self.__get_last_update()
        if (self.last_update.type != new_update.type):
            self.last_update = new_update
            return True
        return False


class UserUpdatesDispatcher:
    subscriptions: list[_UserUpdatesSubscription] = []

    @classmethod
    def set_bot(cls, bot: Bot) -> Self:
        cls.bot = bot
        return cls

    @classmethod
    async def add_subscription(cls, chat_id, shiki_name) -> None:
        cls.subscriptions.append(
            await _UserUpdatesSubscription(chat_id, shiki_name).setup()
        )

    @classmethod
    async def __dispatcher(cls, delay=5) -> None:
        while True:
            for sub in cls.subscriptions:
                if await sub.is_updated():
                    await cls.bot.send_message(
                        chat_id=sub.chat_id,
                        text=str(sub.last_update) + str(sub.user)
                    )
                await asyncio.sleep(delay)
            await asyncio.sleep(delay * 5)

    @classmethod
    async def on_startup(cls):
        asyncio.create_task(cls.__dispatcher())
