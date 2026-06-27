from bs4 import BeautifulSoup, Tag

from extensions.handlers.message.http import HttpExtension
from services.gkfeed import FeedItem

from . import BaseFeedItemView


class ShikiFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_shiki_item(self, item: FeedItem) -> None:
        soup = await self._get_soup(item.link)

        media_url = self._get_media_url(soup)
        description = item.text
        title_name = self._get_title_name(soup)

        await self._send_photo(item, media_url, description, title_name)

    def _get_media_url(self, soup: BeautifulSoup) -> str:
        poster_img = soup.select_one(".b-db_entry-poster picture img")
        if isinstance(poster_img, Tag):
            src = poster_img.get("src")
            if isinstance(src, str):
                return self._normalize_media_url(src)

        poster_meta = soup.find("meta", attrs={"itemprop": "image"})
        if isinstance(poster_meta, Tag):
            content = poster_meta.get("content")
            if isinstance(content, str):
                return self._normalize_media_url(content)

        picture_tag = soup.find("picture")
        if isinstance(picture_tag, Tag):
            source_tag = picture_tag.source
            if isinstance(source_tag, Tag):
                srcset = source_tag.get("srcset")
                if isinstance(srcset, list):
                    srcset = srcset[0]

                if isinstance(srcset, str):
                    return self._normalize_media_url(srcset.split(" ")[-2])

        meta_tag = soup.find("meta", attrs={"property": "og:image"})
        if isinstance(meta_tag, Tag):
            content = meta_tag.get("content")
            if isinstance(content, str):
                return self._normalize_media_url(content)

        raise ValueError("media url not found")

    @staticmethod
    def _normalize_media_url(url: str) -> str:
        if url.startswith("http://"):
            return f"https://{url.removeprefix('http://')}"
        return url

    def _get_title_name(self, soup: BeautifulSoup) -> str:
        h1_tag = soup.find("h1")
        if not isinstance(h1_tag, Tag):
            raise ValueError("h1 tag not found")
        return h1_tag.text.split("/")[0]
