from aiogram import Bot, F, Router
from aiogram.types import BufferedInputFile, Message

from services.jutsu import InvalidUrl, JutSuDownloader


async def download_video(message: Message, bot: Bot) -> None:
    await message.delete()

    if not message.text or not message.chat:
        raise ValueError("Message text or chat is missing")

    try:
        video_data = await JutSuDownloader.download_video(message.text)
        await bot.send_video(
            chat_id=message.chat.id,
            video=BufferedInputFile(video_data, "video.mp4"),
            caption=message.text,
            request_timeout=10000,
        )
    except InvalidUrl:
        await message.answer("Не получилось скачать " + message.text)


def setup(r: Router) -> None:
    r.message.register(download_video, F.text.startswith("https://jut.su/"))
