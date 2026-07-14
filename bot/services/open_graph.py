from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

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
    async def get(cls, url: str) -> OpenGraphMetadata:
        soup = await cls.get_soup(url)
        return cls.parse_soup(soup)

    @staticmethod
    async def get_soup(
        url: str,
        *,
        use_downloader: bool = False,
    ) -> BeautifulSoup:
        if use_downloader:
            html = await HttpService.get_with_downloader(
                url,
                headers=_TWITTERBOT_HEADERS,
            )
        else:
            html = await HttpService.get(url, headers=_TWITTERBOT_HEADERS)

        return BeautifulSoup(html, "html.parser")

    @classmethod
    def parse(cls, html: bytes | str) -> OpenGraphMetadata:
        soup = BeautifulSoup(html, "html.parser")
        return cls.parse_soup(soup)

    @classmethod
    def parse_soup(cls, soup: BeautifulSoup) -> OpenGraphMetadata:
        return OpenGraphMetadata(
            image_url=cls._get_property(soup, "og:image"),
            title=cls._get_property(soup, "og:title"),
            description=cls._get_property(soup, "og:description"),
            video_url=cls._get_property(soup, "og:video"),
        )

    @staticmethod
    def _get_property(
        soup: BeautifulSoup,
        property_name: str,
    ) -> str | None:
        tag = soup.find("meta", attrs={"property": property_name})
        if not isinstance(tag, Tag):
            return None

        content = tag.get("content")
        if not isinstance(content, str):
            return None

        content = content.strip()
        return content or None
