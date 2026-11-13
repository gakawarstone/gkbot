from collections.abc import Awaitable, Callable

from services.gkfeed import FeedItem, GkfeedApi, GkfeedCredentials

from .matching import matches_source_url
from .registry import FeedProcessor
from .rendering import FeedRendering
from .video import send_video


def create_stories_processor(
    rendering: FeedRendering,
    get_credentials: Callable[[], Awaitable[GkfeedCredentials]],
) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        api = GkfeedApi(await get_credentials())
        data = await api.get_raw_item_data(item.id)
        caption = data["feed"]["url"].split("/")[-1]
        await send_video(rendering, item, item.link, link_caption=caption)

    return FeedProcessor(
        "stories",
        # Preserve the existing CDN hostname family without matching URL paths.
        lambda item: matches_source_url(item, host_prefix="stor"),
        process,
    )
