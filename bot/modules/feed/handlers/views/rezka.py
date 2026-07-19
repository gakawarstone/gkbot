from urllib.parse import urlsplit, urlunsplit

from services.gkfeed import FeedItem
from services.open_graph import OpenGraphService

from . import BaseFeedItemView

_PREVIEW_HEADERS = {
    "User-Agent": "TelegramBot (like TwitterBot)",
}


class RezkaFeedItemView(BaseFeedItemView):
    async def _process_rezka_item(self, item: FeedItem) -> None:
        item_url = urlsplit(item.link)
        preview_url = urlunsplit(item_url._replace(netloc="rezka.ag"))
        metadata = await OpenGraphService.get(
            preview_url,
            headers=_PREVIEW_HEADERS,
        )
        if metadata.image_url is None:
            return await self._send_item(item)

        await self._send_photo(item, metadata.image_url, item.title)
