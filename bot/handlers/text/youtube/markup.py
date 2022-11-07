from aiogram import Router
from aiogram.types import Message

from ui.keyboards.youtube import YouTubeMarkup
from filters.youtube import YouTubeVideoLink

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
    r.message.register(add_download_markup, YouTubeVideoLink())
