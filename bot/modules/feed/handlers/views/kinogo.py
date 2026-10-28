from bs4 import BeautifulSoup, Tag

from services.feed_parser import FeedParser
from services.gkfeed import FeedItem
from services.http import HttpService

from . import BaseFeedItemView


class KinogoFeedItemView(BaseFeedItemView):
    async def _process_kinogo_item(self, item: FeedItem) -> None:
        html = await HttpService.get(item.link)
        media_url = await FeedParser.run(KinogoFeedItemView._get_kinogo_media_url, html)
        if not media_url:
            return await self._send_item(item)

        await self._send_photo(item, media_url, "")

    @staticmethod
    def _get_kinogo_media_url(html: bytes) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        link = soup.find("link")
        if not isinstance(link, Tag):
            return None

        media_url = link.get("href")
        return str(media_url) if media_url else None
