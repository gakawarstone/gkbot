from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension
from . import BaseFeedItemView


class SpotiFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_spoti_item(self, item: FeedItem):
        soup = self._get_soup(item.link)

        meta_tag = soup.find("meta", attrs={"name": "twitter:image"})
        media_url = meta_tag["content"]

        description = soup.find("meta", attrs={"name": "twitter:description"})[
            "content"
        ]
        title = soup.find("meta", attrs={"name": "twitter:title"})["content"]
        await self._send_photo(item, media_url, title + "\n" + description)
