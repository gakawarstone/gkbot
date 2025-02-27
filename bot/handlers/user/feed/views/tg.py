from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension

from . import BaseFeedItemView


class TelegramFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_telegram_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)

        meta_tag = soup.find("meta", attrs={"property": "og:image"})
        media_url = meta_tag["content"]

        description = soup.find("meta", attrs={"property": "og:description"})["content"]
        description = self._limit_description(description)
        await self._send_photo(item, media_url, description)

    def _limit_description(self, description: str, limit: int = 500) -> str:
        if len(description) > limit:
            description = description[: limit - 3] + "..."

        return description
