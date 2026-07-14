from services.gkfeed import FeedItem
from services.open_graph import OpenGraphService
from modules.feed.handlers.views.base import BaseWebFeedItemView
from modules.feed.ui.keyboards.porno365 import Porno365FeedItemMarkup


class Porno365FeedItemView(BaseWebFeedItemView):
    async def _process_porno365_item(self, item: FeedItem):
        metadata = await OpenGraphService.get(item.link)
        if metadata.image_url is None:
            return await self._send_item(item)

        await self._send_photo(
            item,
            metadata.image_url,
            metadata.title or item.title,
            link_caption="porno365",
            reply_markup=Porno365FeedItemMarkup.get_item_markup(item.id, item.link),
        )
