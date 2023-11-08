import random

from aiogram import Router, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.exceptions import TelegramBadRequest

from extensions.handlers.query.failed import get_failed_result


async def send_chance(query: InlineQuery):
    message = f"Шанс того что {' '.join(query.query.split(' ')[1:])}: "
    chance = random.randint(0, 100)
    description = "tap to send your chance"

    results = []
    try:
        results += [
            InlineQueryResultArticle(
                id=query.query,
                title=message,
                input_message_content=InputTextMessageContent(
                    message_text=message + str(chance) + "%"
                ),
                description=description,
            )
        ]
    except TelegramBadRequest:
        results += [
            get_failed_result(
                query=query,
                message=f"query message is too long",
                description="try to send link direct to bot",
            ),
        ]

    return await query.answer(
        results=results,
        cache_time=24 * 60 * 60,
        is_personal=False,
    )


def setup(router: Router):
    router.inline_query.register(send_chance, F.query.startswith(("ch", "ч")))
