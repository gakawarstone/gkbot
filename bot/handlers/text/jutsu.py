from aiogram import Router, F
from aiogram.types import Message

from services.jutsu import JutSuDownloader, InvalidUrl

F: Message


async def download_video(message: Message):
    await message.delete()
    try:
        input_file = await JutSuDownloader.download_video(message.text)
        await message.answer_video(input_file, caption=message.text)
    except InvalidUrl:
        await message.answer('Не получилось скачать ' + message.text)


def setup(r: Router):
    r.message.register(
        download_video,
        F.text.startswith('https://jut.su/')
    )
