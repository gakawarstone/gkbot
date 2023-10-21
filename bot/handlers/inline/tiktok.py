from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultVideo

from services.tiktok import TikTokService, TikTokVideoUrlExtractionFailed
from contrib.handlers.query.failed import get_failed_result
from filters.tiktok import TikTokVideoLink


async def send_tiktok(query: InlineQuery):
    results = []
    try:
        video_url = await TikTokService.get_video_url(query.query)
        results += [
            InlineQueryResultVideo(
                id=query.query,
                type="video",
                title="Tiktok video",
                description="tap to send",
                video_url=video_url,
                mime_type="video/mp4",
                thumbnail_url=video_url,
                thumb_url=video_url,
                caption=query.query,
            ),
        ]
    except TikTokVideoUrlExtractionFailed:
        print("failed")
        results += [
            get_failed_result(
                query=query,
                message=f"download failed: {query.query} try to send this link direct to bot",
                description="try to send link direct to bot",
            ),
        ]

    return await query.answer(
        results=results,
        cache_time=24 * 60 * 60,
        is_personal=False,
    )


def setup(router: Router):
    router.inline_query.register(send_tiktok, TikTokVideoLink())
