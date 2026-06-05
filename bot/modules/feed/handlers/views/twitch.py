from urllib.parse import urlparse

from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension
from . import BaseFeedItemView


class TwitchFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_twitch_item(self, item: FeedItem):
        streamer_name = urlparse(item.link).path.strip("/").split("/", 1)[0]
        if not streamer_name:
            raise ValueError("Failed to extract Twitch channel from item link")

        thumbnail_url = f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{streamer_name}-1920x1080.jpg"

        await self._send_photo(
            item,
            thumbnail_url,
            item.text or item.title,
            streamer_name,
        )
