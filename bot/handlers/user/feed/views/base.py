from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension
from . import BaseFeedItemView


class BaseWebFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_base_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)
        meta_tag = soup.find("meta", attrs={"property": "og:image"})
        media_url = meta_tag["content"]
        title = soup.find("title").text
        await self._send_photo(item, media_url, title)
        return
