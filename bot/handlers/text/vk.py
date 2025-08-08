from aiogram import Router
from aiogram.types import Message

from filters.vk import VkVideoLink
from ui.keyboards.vk import VkMarkup


async def add_download_markup(message: Message):
    await message.delete()

    if not message.text:
        raise ValueError("Message text is empty")

    url = message.text
    await message.answer(
        url,
        reply_markup=VkMarkup.get_download_dialog(url),
    )


def setup(r: Router):
    r.message.register(add_download_markup, VkVideoLink())
