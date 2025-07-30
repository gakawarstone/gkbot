from aiogram import Router
from aiogram.types import Message
from aiogram.filters import or_f

# from services.vk import VKService
from ui.keyboards.ytdlp import YtdlpMarkup
from filters.youtube import YouTubeVideoLink
from filters.vk import VkVideoLink


async def add_download_markup(message: Message):
    await message.delete()
    url = message.text if message.text else ""
    # FIXME: VKDOWNLOAD
    # if url.startswith("https://vk.com/wall"):
    #     url = await VKService.try_to_extract_video_link_from_post(url)

    yt_code = url.split("v=")[-1]

    await message.answer(
        url,
        reply_markup=YtdlpMarkup.get_download_dialog(
            yt_code,
        ),
    )


def setup(r: Router):
    filter = or_f(YouTubeVideoLink(), VkVideoLink())
    r.message.register(add_download_markup, filter)
