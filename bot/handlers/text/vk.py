from aiogram import Router
from aiogram.types import Message

from filters.vk import VkVideoLink
from ui.keyboards.vk import VkMarkup
from utils.vk import parse_vk_reference


async def add_download_markup(message: Message) -> None:
    await message.delete()

    if not message.text:
        raise ValueError("Message text is empty")

    url = message.text
    reference = parse_vk_reference(url)
    await message.answer(
        url,
        reply_markup=VkMarkup.get_download_dialog(reference),
    )


def setup(r: Router) -> None:
    r.message.register(add_download_markup, VkVideoLink())
