from aiogram import Router
from aiogram.types import Message

from services.llm import Gemini
from filters.command import CommandWithPrompt


async def send_llm_answer(m: Message):
    await m.delete()

    if not m.text:
        raise ValueError("Message text cannot be empty")

    command_args = m.text.split(" ")[1:]
    prompt = " ".join(command_args)

    _message = await m.answer("Подождите..")
    text = ""
    async for ch in Gemini().stream(prompt):
        text += ch.text
        await _message.edit_text(text)


async def send_unavailable_message(m: Message):
    await m.delete()
    await m.answer("this function is unavailable")


def setup(r: Router):
    r.message.register(send_llm_answer, CommandWithPrompt("gpt"))
