from aiogram import Router
from aiogram.types import Message
from aiogram.filters import or_f

from ui.keyboards.ytdlp import YtdlpMarkup
from filters.youtube import YouTubeVideoLink
from filters.vk import VkVideoLink

F: Message


async def add_download_markup(message: Message):
    await message.answer(
        message.text,
        reply_markup=YtdlpMarkup.get_download_mp3_dialog(
            user_id=message.from_user.id,
            message_id=message.message_id
        )
    )


def setup(r: Router):
    filter = or_f(YouTubeVideoLink(), VkVideoLink())
    r.message.register(add_download_markup, filter)
