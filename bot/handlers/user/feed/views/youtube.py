from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension
from . import BaseFeedItemView


class YoutubeFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_youtube_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)

        video_code = item.link.split("=")[-1]
        media_url = f"https://i3.ytimg.com/vi/{video_code}/maxresdefault.jpg"
        title = soup.find("title").text
        await self._send_photo(item, media_url, title)
        return
