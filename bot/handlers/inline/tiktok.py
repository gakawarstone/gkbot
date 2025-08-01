import hashlib

from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultVideo

from services.tiktok import (
    TikTokService,
    TikTokVideoUrlExtractionFailed,
    TikTokInfoExtractionFailed,
)
from extensions.handlers.query.failed import async_return_failed_result_if
from filters.tiktok import TikTokVideoLink
from ._types import ResultsType


@async_return_failed_result_if(
    exceptions_to_handle=[TikTokVideoUrlExtractionFailed, TikTokInfoExtractionFailed],
    message_to_send="download failed: {} try to send this link direct to bot",
    description="try to send link direct to bot",
)
async def _get_results(query: InlineQuery) -> ResultsType:
    video_url = await TikTokService.get_video_url(query.query.split(" ")[0])
    return [
        InlineQueryResultVideo(
            id=hashlib.md5(query.query.encode()).hexdigest(),
            title="Tiktok video",
            description="tap to send",
            video_url=video_url,
            mime_type="video/mp4",
            thumbnail_url=video_url,
            thumb_url=video_url,
            caption=query.query,
        ),
    ]


async def send_tiktok(query: InlineQuery):
    results: ResultsType = await _get_results(query)
    return await query.answer(
        results=results,
        cache_time=24 * 60 * 60,
        is_personal=False,
    )


def setup(router: Router):
    router.inline_query.register(send_tiktok, TikTokVideoLink())
