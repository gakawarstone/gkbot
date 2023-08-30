from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultVideo

from services.tiktok import TikTokService
from filters.tiktok import TikTokVideoLink


async def send_tiktok(query: InlineQuery):
    video_url = await TikTokService.get_video_url(query.query)
    return await query.answer(
        results=[
            InlineQueryResultVideo(
                id=query.query,
                type='video',
                title='Tiktok video',
                description='tap to send',
                video_url=video_url,
                mime_type='video/mp4',
                thumbnail_url=video_url,
                thumb_url=video_url,
                caption=query.query,
            ),
        ],
        cache_time=60,
        is_personal=True
    )


def setup(router: Router):
    router.inline_query.register(
        send_tiktok,
        TikTokVideoLink()
    )
