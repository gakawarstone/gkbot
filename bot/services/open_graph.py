from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

from services.feed_parser import feed_parser
from services.http import HttpService

_TWITTERBOT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Twitterbot/1.0)",
}


@dataclass(frozen=True, slots=True)
class OpenGraphMetadata:
    image_url: str | None
    title: str | None
    description: str | None
    video_url: str | None


class OpenGraphService:
    @classmethod
    async def get(
        cls,
        url: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> OpenGraphMetadata:
        html = await cls.get_html(url, headers=headers)
        return await feed_parser.run(cls.parse, html)

    @staticmethod
    async def get_html(
        url: str,
        *,
        headers: dict[str, str] | None = None,
        use_downloader: bool = False,
    ) -> bytes:
        request_headers = headers or _TWITTERBOT_HEADERS
        if use_downloader:
            html = await HttpService.get_with_downloader(
                url,
                headers=request_headers,
            )
        else:
            html = await HttpService.get(url, headers=request_headers)

        return html

    @classmethod
    def parse(cls, html: bytes | str) -> OpenGraphMetadata:
        soup = BeautifulSoup(html, "html.parser")
        return cls.parse_soup(soup)

    @classmethod
    def parse_soup(cls, soup: BeautifulSoup) -> OpenGraphMetadata:
        return OpenGraphMetadata(
            image_url=cls._get_property(soup, "og:image", "twitter:image"),
            title=cls._get_property(soup, "og:title", "twitter:title"),
            description=cls._get_property(
                soup,
                "og:description",
                "twitter:description",
            ),
            video_url=cls._get_property(soup, "og:video", "twitter:player"),
        )

    @staticmethod
    def _get_property(
        soup: BeautifulSoup,
        property_name: str,
        fallback_name: str,
    ) -> str | None:
        metadata_names = (
            ("property", property_name),
            ("name", fallback_name),
        )
        for attribute_name, metadata_name in metadata_names:
            tag = soup.find("meta", attrs={attribute_name: metadata_name})
            if not isinstance(tag, Tag):
                continue

            value = tag.get("content") or tag.get("value")
            if isinstance(value, str) and (value := value.strip()):
                return value

        return None
