import random
import hashlib

from aiogram import Router, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent


async def send_chance(query: InlineQuery):
    message = f"Шанс того что {' '.join(query.query.split(' ')[1:])}: "
    chance = random.randint(0, 100)
    description = "tap to send your chance"

    results = [
        InlineQueryResultArticle(
            id=hashlib.md5(query.query.encode()).hexdigest(),
            title=message,
            input_message_content=InputTextMessageContent(
                message_text=message + str(chance) + "%"
            ),
            description=description,
        )
    ]

    return await query.answer(
        results=results,
        cache_time=24 * 60 * 60,
        is_personal=False,
    )


def setup(router: Router):
    router.inline_query.register(send_chance, F.query.startswith(("ch", "ч")))
