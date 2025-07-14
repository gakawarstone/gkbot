from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError


class Notifier:
    @classmethod
    async def setup(cls, bot: Bot) -> None:
        cls.__bot = bot

    @classmethod
    async def notify(cls, chat_id: int, text: str) -> None:
        try:
            await cls.__bot.send_message(chat_id, text)
        except TelegramForbiddenError:
            print(f"user with id: {chat_id} blocked bot")
