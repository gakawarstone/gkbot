from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension
from bs4 import Tag

from . import BaseFeedItemView


class TelegramFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_telegram_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)

        meta_tag = soup.find("meta", attrs={"property": "og:image"})
        if not isinstance(meta_tag, Tag):
            return await self._send_item(item)

        media_url = meta_tag.get("content")
        if not media_url:
            return await self._send_item(item)

        description_tag = soup.find("meta", attrs={"property": "og:description"})
        if not isinstance(description_tag, Tag):
            return await self._send_item(item)

        description = str(description_tag.get("content"))
        description = self._limit_description(description)

        await self._send_photo(item, str(media_url), description)

    def _limit_description(self, description: str, limit: int = 250) -> str:
        if len(description) > limit:
            description = description[: limit - 3] + "..."

        return description
