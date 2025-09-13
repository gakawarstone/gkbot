from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension
from . import BaseFeedItemView


class TwitchFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_twitch_item(self, item: FeedItem):
        data = await (await self._gkfeed()).get_raw_item_data(item.id)

        streamer_name = data["item"]["title"].split(":")[0]
        thumbnail_url = f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{streamer_name}-1920x1080.jpg"

        await self._send_photo(
            item,
            thumbnail_url,
            data["item"]["text"],
            streamer_name,
        )
