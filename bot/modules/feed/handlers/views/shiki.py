from bs4 import BeautifulSoup, Tag

from services.feed_parser import FeedParser
from services.gkfeed import FeedItem
from services.http import HttpService

from . import BaseFeedItemView


class ShikiFeedItemView(BaseFeedItemView):
    async def _process_shiki_item(self, item: FeedItem) -> None:
        html = await HttpService.get(item.link)
        media_url, title_name = await FeedParser.run(
            ShikiFeedItemView._parse_shiki_page, html
        )
        description = item.text

        await self._send_photo(item, media_url, description, title_name)

    @classmethod
    def _parse_shiki_page(cls, html: bytes) -> tuple[str, str]:
        soup = BeautifulSoup(html, "html.parser")
        return cls._get_media_url(soup), cls._get_title_name(soup)

    @classmethod
    def _get_media_url(cls, soup: BeautifulSoup) -> str:
        poster_img = soup.select_one(".b-db_entry-poster picture img")
        if isinstance(poster_img, Tag):
            src = poster_img.get("src")
            if isinstance(src, str) and src.strip():
                return cls._normalize_media_url(src)

        poster_meta = soup.find("meta", attrs={"itemprop": "image"})
        if isinstance(poster_meta, Tag):
            content = poster_meta.get("content")
            if isinstance(content, str) and content.strip():
                return cls._normalize_media_url(content)

        picture_tag = soup.find("picture")
        if isinstance(picture_tag, Tag):
            source_tag = picture_tag.source
            if isinstance(source_tag, Tag):
                srcset = source_tag.get("srcset")
                if isinstance(srcset, list):
                    srcset = srcset[0]

                if isinstance(srcset, str) and srcset.strip():
                    candidates = srcset.rsplit(",", maxsplit=1)
                    media_url = candidates[-1].strip().split()[0]
                    return cls._normalize_media_url(media_url)

        meta_tag = soup.find("meta", attrs={"property": "og:image"})
        if isinstance(meta_tag, Tag):
            content = meta_tag.get("content")
            if isinstance(content, str) and content.strip():
                return cls._normalize_media_url(content)

        raise ValueError("media url not found")

    @staticmethod
    def _normalize_media_url(url: str) -> str:
        media_url = url.strip()
        if media_url.startswith("//"):
            return f"https:{media_url}"
        return media_url

    @staticmethod
    def _get_title_name(soup: BeautifulSoup) -> str:
        h1_tag = soup.find("h1")
        if not isinstance(h1_tag, Tag):
            raise TypeError("h1 tag not found")

        title = h1_tag.get_text(" ", strip=True).partition("/")[0].strip()
        if not title:
            raise ValueError("title name not found")
        return title
