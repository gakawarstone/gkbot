from pprint import pprint

from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle

from lib.bot import BotManager

router = Router()


@router.inline_query()
async def echo(query: InlineQuery):
    pprint(query)
    return await query.answer([InlineQueryResultArticle(title='text')],
                              switch_pm_text='test')


def setup(mng: BotManager):
    mng.dp.register_inline_query(
        echo
    )
    mng.dp.include_router(router)
