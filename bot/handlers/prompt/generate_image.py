import asyncio
import random

from aiogram import Router
from aiogram.types import (
    Message,
    BufferedInputFile,
    InputMediaPhoto,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaVideo,
)

from filters.command import CommandWithPrompt
from services.agents.image_prompt_enhancer import ImagePromptEnhancer
from services.http import HttpService

_MEDIA_GROUP = list[
    InputMediaAudio | InputMediaDocument | InputMediaPhoto | InputMediaVideo
]


async def generate_image(m: Message):
    await m.delete()

    if not m.text:
        return

    prompt = " ".join(m.text.split(" ")[1:])
    prompt = await ImagePromptEnhancer.enhance(prompt)

    tasks = []
    async with asyncio.TaskGroup() as tg:
        for _ in range(4):
            img_url = _generate_url(prompt)
            tasks.append(tg.create_task(HttpService.get(img_url)))

    media_group: _MEDIA_GROUP = [
        InputMediaPhoto(media=BufferedInputFile(task.result(), "image.jpg"))
        for task in tasks
    ]

    await m.answer_media_group(media_group)


def _generate_url(prompt: str) -> str:
    img_url = f"https://image.pollinations.ai/prompt/{prompt}".replace(" ", "+").strip()
    img_url += "?width=1024"
    img_url += "&height=1024"
    img_url += "&model=flux"
    img_url += "&nologo=true"
    img_url += "&private=false"
    img_url += "&enhance=false"
    img_url += "&safe=false"
    img_url += f"&seed={random.randint(10**9, 10**10 - 1)}"
    return img_url


def setup(r: Router):
    r.message.register(generate_image, CommandWithPrompt("img"))
