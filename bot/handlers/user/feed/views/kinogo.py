from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension
from . import BaseFeedItemView


class KinogoFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_kinogo_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)

        link = soup.find("link")
        media_url = link["href"]

        await self._send_photo(item, media_url, "")
