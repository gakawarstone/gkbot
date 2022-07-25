from pprint import pprint

from aiogram import Router
from aiogram.types import (InlineQuery, InlineQueryResultArticle,
                           InlineQueryResultPhoto, InputTextMessageContent,
                           InlineQueryResult, InputMessageContent, InlineQueryResultVideo)
from lib.bot import BotManager

router = Router()


@router.inline_query()
async def prefix_handler(query: InlineQuery):
    if query.query.startswith('b:'):
        answers = [
            InlineQueryResultArticle(
                id='b',
                type='article',
                title='bomber',
                description='bomb it',
                input_message_content=InputTextMessageContent(
                    message_text='/bomber'
                )

            )
        ]

    return await query.answer(
        answers,
        cache_time=60,
        is_personal=True
    )


def setup(mng: BotManager):
    mng.dp.include_router(router)
