import random

from aiogram import F, Router
from aiogram.types import InlineQuery

from ._article import answer_article


async def send_chance(query: InlineQuery) -> bool:
    message = f"Шанс того что {' '.join(query.query.split(' ')[1:])}: "
    chance = random.randint(0, 100)

    return await answer_article(
        query,
        title=message,
        message_text=message + str(chance) + "%",
        description="tap to send your chance",
        cache_time=24 * 60 * 60,
    )


def setup(router: Router) -> None:
    router.inline_query.register(send_chance, F.query.startswith(("ch", "ч")))
