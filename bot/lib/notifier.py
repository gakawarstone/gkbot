from aiogram import Bot


class Notifier:
    @classmethod
    async def setup(cls, bot: Bot) -> None:
        cls.__bot = bot

    @classmethod
    async def notify(cls, chat_id: int, text: str) -> None:
        await cls.__bot.send_message(chat_id, text)
