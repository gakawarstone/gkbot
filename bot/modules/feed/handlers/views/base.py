from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension
from bs4 import Tag
from . import BaseFeedItemView


class BaseWebFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_base_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)

        meta_tag = soup.find("meta", attrs={"property": "og:image"})
        if not isinstance(meta_tag, Tag):
            return await self._send_item(item)

        media_url = meta_tag.get("content")
        if not media_url:
            return await self._send_item(item)

        title_tag = soup.find("title")
        title = title_tag.text if isinstance(title_tag, Tag) else ""
        await self._send_photo(item, str(media_url), str(title))
