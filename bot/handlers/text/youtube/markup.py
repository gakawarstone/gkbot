from aiogram import Router, F
from aiogram.types import Message

from ui.keyboards.youtube import YouTubeMarkup

F: Message


async def add_download_markup(message: Message):
    await message.answer(
        message.text,
        reply_markup=YouTubeMarkup.get_download_mp3_dialog(
            user_id=message.from_user.id,
            message_id=message.message_id
        )
    )


def setup(r: Router):
    r.message.register(
        add_download_markup,
        F.text.startswith('https://www.youtube.com')
    )
