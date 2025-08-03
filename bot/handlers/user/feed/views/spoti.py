from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension
from bs4 import Tag
from . import BaseFeedItemView


class SpotiFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_spoti_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)

        meta_tag = soup.find("meta", attrs={"name": "twitter:image"})
        if not isinstance(meta_tag, Tag):
            return await self._send_item(item)

        media_url = meta_tag.get("content")
        if not media_url:
            return await self._send_item(item)

        title_tag = soup.find("meta", attrs={"name": "twitter:title"})
        if not isinstance(title_tag, Tag):
            return await self._send_item(item)
        title = str(title_tag.get("content") or "")

        description_tag = soup.find("meta", attrs={"name": "twitter:description"})
        if not isinstance(description_tag, Tag):
            return await self._send_item(item)
        description = str(description_tag.get("content") or "")

        await self._send_photo(item, str(media_url), title + "\n" + description)
