from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultVideo

from services.tiktok import TikTokService, TikTokVideoUrlExtractionFailed
from extensions.handlers.query.failed import async_return_failed_result_if
from filters.tiktok import TikTokVideoLink


@async_return_failed_result_if(
    exceptions_to_handle=[
        TikTokVideoUrlExtractionFailed,
    ],
    message_to_send="download failed: {query} try to send this link direct to bot",
    description="try to send link direct to bot",
)
async def _get_results(query: InlineQuery) -> list[InlineQueryResultVideo]:
    video_url = await TikTokService.get_video_url(query.query)
    return [
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


async def send_tiktok(query: InlineQuery):
    results = await _get_results(query)
    return await query.answer(
        results=results,
        cache_time=24 * 60 * 60,
        is_personal=False,
    )


def setup(router: Router):
    router.inline_query.register(send_tiktok, TikTokVideoLink())
