from services.gkfeed import FeedItem
from services.open_graph import OpenGraphService

from . import BaseFeedItemView


class TelegramFeedItemView(BaseFeedItemView):
    async def _process_telegram_item(self, item: FeedItem):
        metadata = await OpenGraphService.get(item.link)
        if metadata.image_url is None or metadata.description is None:
            return await self._send_item(item)

        description = self._limit_description(metadata.description)

        await self._send_photo(item, metadata.image_url, description)

    def _limit_description(self, description: str, limit: int = 250) -> str:
        if len(description) > limit:
            description = description[: limit - 3] + "..."

        return description
