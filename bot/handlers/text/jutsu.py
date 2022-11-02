from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from services.jutsu import JutSuDownloader, InvalidUrl

F: Message


async def download_video(message: Message, state: FSMContext):
    await message.delete()
    try:
        input_file = await JutSuDownloader.download_video(message.text)
        await state.bot.send_video(
            chat_id=message.chat.id,
            video=input_file,
            caption=message.text,
            request_timeout=10000
        )
    except InvalidUrl:
        await message.answer('Не получилось скачать ' + message.text)


def setup(r: Router):
    r.message.register(
        download_video,
        F.text.startswith('https://jut.su/')
    )
