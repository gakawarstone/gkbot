from aiogram import Router
from aiogram.types import Message
from g4f import ChatCompletion

from filters.command import CommandWithPrompt


async def send_llm_answer(m: Message):
    await m.delete()
    command_args = m.text.split(" ")[1:]
    text = " ".join(command_args)

    response = await ChatCompletion.create_async(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": f"Ты поисковик и выдаешь один абзац текста по запросу отвечай на русском: {text}",
            }
        ],
    )
    await m.answer(response)


def setup(r: Router):
    r.message.register(send_llm_answer, CommandWithPrompt("gpt"))
