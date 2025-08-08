from aiogram import Router
from aiogram.types import Message

from filters.youtube import YouTubeVideoLink
from ui.keyboards.ytdlp import YtdlpMarkup


async def add_download_markup(message: Message):
    await message.delete()

    if not message.text:
        raise ValueError("Message text is empty")
    url = message.text

    if url.startswith("https://youtu.be/"):
        yt_code = url.split("/")[-1].split("?")[0]
    else:
        yt_code = url.split("v=")[-1]

    await message.answer(
        url,
        reply_markup=YtdlpMarkup.get_download_dialog(
            yt_code,
        ),
    )


def setup(r: Router):
    r.message.register(add_download_markup, YouTubeVideoLink())
