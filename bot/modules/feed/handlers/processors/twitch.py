from urllib.parse import urlparse

from services.gkfeed import FeedItem

from .._exceptions import FeedMediaExtractionError
from ._simple_rendering import SendPhoto
from .registry import FeedProcessor


def _matches_twitch(item: FeedItem) -> bool:
    return item.link.startswith("https://www.twitch")


def create_twitch_processor(send_photo: SendPhoto) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        streamer_name = urlparse(item.link).path.strip("/").split("/", 1)[0]
        if not streamer_name:
            raise FeedMediaExtractionError(
                "Failed to extract Twitch channel from item link"
            )

        thumbnail_url = f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{streamer_name}-1920x1080.jpg"
        await send_photo(item, thumbnail_url, item.text or item.title, streamer_name)

    return FeedProcessor("twitch", _matches_twitch, process)
