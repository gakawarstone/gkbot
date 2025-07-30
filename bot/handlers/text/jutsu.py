from aiogram import Router, F, Bot
from aiogram.types import Message

from services.jutsu import JutSuDownloader, InvalidUrl


async def download_video(message: Message, bot: Bot):
    await message.delete()

    if not message.text or not message.chat:
        raise ValueError("Message text or chat is missing")

    try:
        input_file = await JutSuDownloader.download_video(message.text)
        await bot.send_video(
            chat_id=message.chat.id,
            video=input_file,
            caption=message.text,
            request_timeout=10000,
        )
    except InvalidUrl:
        await message.answer("Не получилось скачать " + message.text)


def setup(r: Router):
    r.message.register(download_video, F.text.startswith("https://jut.su/"))
