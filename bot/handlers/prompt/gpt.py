from aiogram import Router
from aiogram.types import Message
from filters.command import CommandWithPrompt
from services.llm import OpenRouter


# DEPRECATED: use /ask instead.
async def send_llm_answer(m: Message):
    await m.delete()

    if not m.text:
        raise ValueError("Message text cannot be empty")

    command_args = m.text.split(" ")[1:]
    prompt = " ".join(command_args)

    _message = await m.answer("Подождите..")
    text = ""
    async for ch in OpenRouter().stream(prompt):
        text += ch.text
        await _message.edit_text(text)


def setup(r: Router):
    r.message.register(send_llm_answer, CommandWithPrompt("gpt"))
