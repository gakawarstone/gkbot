import random

from aiogram import F, Router
from aiogram.types import InlineQuery

from ._article import answer_article


async def send_choice(query: InlineQuery) -> bool | None:
    message = f"Из {', '.join(query.query.split(' ')[1:])} я выбираю: "
    choices = query.query.split(" ")[1:]

    if not choices:
        return None

    choice = random.choice(choices)

    return await answer_article(
        query,
        title=message,
        message_text=message + "\n\n👉 <b>" + str(choice) + "</b>",
        description="tap to send your choice",
        cache_time=10,
    )


def setup(router: Router) -> None:
    router.inline_query.register(send_choice, F.query.startswith(("lst", "лст")))
