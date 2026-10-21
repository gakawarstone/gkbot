from services.gkfeed import FeedItem
from services.open_graph import OpenGraphService

from . import BaseFeedItemView


class BaseWebFeedItemView(BaseFeedItemView):
    async def _process_base_item(self, item: FeedItem):
        metadata = await OpenGraphService.get(item.link)

        if metadata.image_url is None:
            return await self._send_item(item)

        await self._send_photo(
            item,
            metadata.image_url,
            metadata.title or item.title,
        )
