from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension

from . import BaseFeedItemView


class TelegramFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_telegram_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)

        meta_tag = soup.find("meta", attrs={"property": "og:image"})
        if not meta_tag or "content" not in meta_tag.attrs:
            await self._send_item(item)
            return
        media_url = meta_tag["content"]

        description_tag = soup.find("meta", attrs={"property": "og:description"})
        description = ""
        if description_tag and "content" in description_tag.attrs:
            description = description_tag["content"]
        description = self._limit_description(description)

        await self._send_photo(item, media_url, description)

    def _limit_description(self, description: str, limit: int = 250) -> str:
        if len(description) > limit:
            description = description[: limit - 3] + "..."

        return description
