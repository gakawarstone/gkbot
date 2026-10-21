from services.gkfeed import FeedItem, GkfeedApi

from . import BaseFeedItemView
from .video import VideoFeedItemView


class StoriesFeedItemView(VideoFeedItemView, BaseFeedItemView):
    async def _process_stories_item(self, item: FeedItem):
        api = GkfeedApi(await self._gkfeed_credentials)
        data = await api.get_raw_item_data(item.id)
        caption = data["feed"]["url"].split("/")[-1]
        await self._send_video(item, item.link, link_caption=caption)
