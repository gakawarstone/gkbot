from services.gkfeed import FeedItem
from services.tiktok import TikTokService

from ...ui.keyboards import FeedMarkup
from .registry import FeedProcessor
from .rendering import FeedRendering


def create_tiktok_processor(rendering: FeedRendering) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        video = await TikTokService.get_video(item.link)

        await rendering.answer_video(
            video.input_file,
            caption=f'<a href="{item.link}">{item.link.split("@")[1].split("/")[0]}</a>',
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
            height=video.height,
            width=video.width,
            duration=video.duration,
            supports_streaming=True,
        )

    return FeedProcessor(
        "tiktok",
        lambda item: item.link.startswith(("https://www.tiktok",)),
        process,
    )
