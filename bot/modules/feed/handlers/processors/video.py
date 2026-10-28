from aiogram.types import BufferedInputFile

from services.gkfeed import FeedItem
from services.http import HttpService

from ...ui.keyboards import FeedMarkup
from .rendering import FeedRendering


async def send_video(
    rendering: FeedRendering,
    item: FeedItem,
    video_url: str,
    link_caption: str = "Link to video",
) -> None:
    video_url = await HttpService.get_redirected_url(video_url)
    video_data = await HttpService.get(video_url)
    await rendering.answer_video(
        BufferedInputFile(video_data, "video.mp4"),
        caption=f'<a href="{item.link}">{link_caption}</a>',
        reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
    )
