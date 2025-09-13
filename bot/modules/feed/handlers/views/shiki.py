from bs4 import BeautifulSoup, Tag

from extensions.handlers.message.http import HttpExtension
from services.gkfeed import FeedItem

from . import BaseFeedItemView


class ShikiFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_shiki_item(self, item: FeedItem) -> None:
        data = await (await self._gkfeed()).get_raw_item_data(item.id)
        soup = await self._get_soup(item.link)

        media_url = self._get_media_url(soup)
        description = data["item"]["text"]
        title_name = self._get_title_name(soup)

        await self._send_photo(item, media_url, description, title_name)

    def _get_media_url(self, soup: BeautifulSoup) -> str:
        meta_tag = soup.find("meta", attrs={"property": "og:image"})
        if not isinstance(meta_tag, Tag):
            raise ValueError("meta tag not found")

        picture_tag = soup.find("picture")
        if not isinstance(picture_tag, Tag):
            raise ValueError("picture tag not found")

        source_tag = picture_tag.source
        if not isinstance(source_tag, Tag):
            raise ValueError("source tag not found")

        srcset = source_tag.get("srcset")
        if isinstance(srcset, list):
            srcset = srcset[0]

        if not isinstance(srcset, str):
            raise ValueError("srcset not found")

        return srcset.split(" ")[-2]

    def _get_title_name(self, soup: BeautifulSoup) -> str:
        h1_tag = soup.find("h1")
        if not isinstance(h1_tag, Tag):
            raise ValueError("h1 tag not found")
        return h1_tag.text.split("/")[0]
