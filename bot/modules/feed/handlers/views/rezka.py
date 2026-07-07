from urllib.parse import urlsplit, urlunsplit

from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension
from bs4 import Tag
from . import BaseFeedItemView


class RezkaFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_rezka_item(self, item: FeedItem):
        item_url = urlsplit(item.link)
        preview_url = urlunsplit(item_url._replace(netloc="rezka.ag"))
        soup = await self._get_soup(preview_url)

        meta_tag = soup.find("meta", attrs={"property": "og:image"})
        if not isinstance(meta_tag, Tag):
            return await self._send_item(item)

        media_url = meta_tag.get("content")
        if not media_url:
            return await self._send_item(item)

        await self._send_photo(item, str(media_url), item.title)
