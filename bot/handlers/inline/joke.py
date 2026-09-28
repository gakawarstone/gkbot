import random

from aiogram import F, Router
from aiogram.types import InlineQuery

from ui.static import TextFiles

from ._article import answer_article


async def send_joke(query: InlineQuery) -> bool:
    anecdotes = (await TextFiles.anecdotes.as_str()).split("\n\n")
    num = random.randint(0, len(anecdotes))
    anecdote = anecdotes[num]

    return await answer_article(
        query,
        title="Анекдот про штирлица: ",
        message_text=anecdote,
        description=" ".join(anecdote.split(" ")[:3]),
        cache_time=1,
    )


def setup(router: Router) -> None:
    router.inline_query.register(send_joke, F.query.startswith(("joke", "witze")))
