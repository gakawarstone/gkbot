from typing_extensions import Self

from aiogram import Bot


class _NotifierNotInited(Exception):
    def __str__(self) -> str:
        return 'Please run Notifier.setup()'


class Notifier:
    __initialized = False

    @classmethod
    async def setup(cls, bot: Bot, admins: list[int]) -> Self:
        cls.__bot = bot
        cls.__admins = admins
        cls.__initialized = True

    @classmethod
    async def notify_admins(cls, text: str) -> None:
        if not cls.__initialized:
            raise _NotifierNotInited
        for admin_id in cls.__admins:
            await cls.__bot.send_message(admin_id, text)
