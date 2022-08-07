from aiogram import F, Router
from aiogram.types import InlineQuery
from youtube_search import YoutubeSearch
import hashlib
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent

F: InlineQuery


async def youtube_search(query: InlineQuery):
    links = YoutubeSearch(query.query, max_results=10).to_dict()
    await query.answer(
        results=[
            InlineQueryResultArticle(
                id=hashlib.md5(f'{link["id"]}'.encode()).hexdigest(),
                title=f'{link["title"]}',
                description=f'Просмотров: {link["views"].split()[0]}',
                thumb_url=f'{link["thumbnails"][0]}',
                input_message_content=InputTextMessageContent(
                    message_text=f'https://www.youtube.com{link["url_suffix"]}'
                )
            )
            for link in links
        ],
        cache_time=60,
        is_personal=True
    )


def setup(router: Router):
    router.register_inline_query(
        youtube_search,
        F.query.startswith(('y ',  'ю '))
    )
