from services.gkfeed import FeedItem
from services.youtube import YoutubeApiService
from . import BaseFeedItemView


class YoutubeFeedItemView(BaseFeedItemView):
    async def _process_youtube_item(self, item: FeedItem):
        data = await YoutubeApiService.get_video_data(item.link)
        await self._send_photo(item, data.thumbnail_url, data.title, data.channel_title)
