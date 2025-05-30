import random

from aiogram import Router
from aiogram.types import Message, BufferedInputFile

from filters.command import CommandWithPrompt
from services.agents.image_prompt_enhancer import ImagePromptEnhancer
from services.http import HttpService


async def generate_image(m: Message):
    await m.delete()
    prompt = " ".join(m.text.split(" ")[1:])
    prompt = await ImagePromptEnhancer.enhance(prompt)

    img_url = f"https://image.pollinations.ai/prompt/{prompt}".replace(" ", "+").strip()
    img_url += f"?width=1024"
    img_url += f"&height=1024"
    img_url += f"&model=flux"
    img_url += "&nologo=true"
    img_url += "&private=false"
    img_url += "&enhance=false"
    img_url += "&safe=false"
    img_url += f"&seed={random.randint(10**9, 10**10 - 1)}"

    print(img_url)
    content = await HttpService.get(img_url)
    await m.answer_photo(BufferedInputFile(content, "image.jpg"))


def setup(r: Router):
    r.message.register(generate_image, CommandWithPrompt("img"))
