import random
import hashlib

from aiogram import Router, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent


async def send_choice(query: InlineQuery):
    message = f"Из {', '.join(query.query.split(' ')[1:])} я выбираю: "
    choices = query.query.split(" ")[1:]

    if not choices:
        return

    choice = random.choice(choices)
    description = "tap to send your choice"

    results = [
        InlineQueryResultArticle(
            id=hashlib.md5(query.query.encode()).hexdigest(),
            title=message,
            input_message_content=InputTextMessageContent(
                message_text=message + str(choice)
            ),
            description=description,
        )
    ]

    return await query.answer(
        results=results,
        cache_time=10,
        is_personal=False,
    )


def setup(router: Router):
    router.inline_query.register(send_choice, F.query.startswith(("lst", "лст")))
