from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension
from bs4 import Tag
from . import BaseFeedItemView


class KinogoFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_kinogo_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)

        link = soup.find("link")
        if not isinstance(link, Tag):
            return await self._send_item(item)

        media_url = link.get("href")
        if not media_url:
            return await self._send_item(item)

        await self._send_photo(item, str(media_url), "")
