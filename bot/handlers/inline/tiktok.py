from aiogram import F, Router
from aiogram.types import InlineQuery

from lib.bot import BotManager
from services.tiktok import TikTokDownloader


F: InlineQuery
router = Router()


@router.inline_query(
    F.query.startswith('https://vm.tiktok.com/')
)
async def send_tiktok(query: InlineQuery):
    return await query.answer(
        [TikTokDownloader.get_as_query_result(query.query)],
        cache_time=60,
        is_personal=True
    )


def setup(mng: BotManager):
    mng.dp.include_router(router)
