from typing import Any
from aiogram import Router, F
from aiogram.types import InlineQuery
from youtube_search import YoutubeSearch
import hashlib
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent


async def youtube_search(query: InlineQuery):
    raw_links = YoutubeSearch(query.query, max_results=10).to_dict()
    if not isinstance(raw_links, list):
        raise ValueError("Invalid response from YoutubeSearch")

    links: list[dict[str, Any]] = raw_links

    await query.answer(
        results=[
            InlineQueryResultArticle(
                id=hashlib.md5(f'{link["id"]}'.encode()).hexdigest(),
                title=f'{link["title"]}',
                description=f'Просмотров: {link["views"].split()[0]}',
                thumb_url=f'{link["thumbnails"][0]}',
                input_message_content=InputTextMessageContent(
                    message_text=f'https://www.youtube.com{link["url_suffix"]}'
                ),
            )
            for link in links
        ],
        cache_time=60,
        is_personal=True,
    )


def setup(router: Router):
    router.inline_query.register(youtube_search, F.query.startswith(("y ", "ю ")))
