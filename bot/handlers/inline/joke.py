import random
import hashlib

from aiogram import Router, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from ui.static import TextFiles


async def send_joke(query: InlineQuery):
    anecdotes = (await TextFiles.anecdotes.as_str()).split("\n\n")
    num = random.randint(0, len(anecdotes))
    anecdote = anecdotes[num]
    message = "Анекдот про штирлица: "
    description = " ".join(anecdote.split(" ")[:3])

    results = [
        InlineQueryResultArticle(
            id=hashlib.md5(query.query.encode()).hexdigest(),
            title=message,
            input_message_content=InputTextMessageContent(message_text=anecdote),
            description=description,
        )
    ]

    return await query.answer(
        results=results,
        cache_time=1,
        is_personal=False,
    )


def setup(router: Router):
    router.inline_query.register(send_joke, F.query.startswith(("joke", "witze")))
