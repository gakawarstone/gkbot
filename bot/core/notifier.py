from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from configs.admins import ADMINS


class Notifier:
    @classmethod
    async def setup(cls, bot: Bot) -> None:
        cls.__bot = bot

    @classmethod
    async def notify(cls, chat_id: int, text: str) -> None:
        if chat_id in ADMINS:
            type_chat_id = "admin"
        else:
            type_chat_id = "user"

        try:
            await cls.__bot.send_message(chat_id, text)
        except TelegramForbiddenError:
            print(f"{type_chat_id} with id: {chat_id} blocked bot")
