from bs4 import BeautifulSoup, Tag

from services.http import HttpService


class Porno365Service:
    _quality_order = ("1080p", "hd", "hq", "sd", "lq")

    @classmethod
    async def get_best_video_url(cls, page_url: str) -> str:
        html = await HttpService.get(page_url)
        soup = BeautifulSoup(html, "html.parser")
        urls_by_quality = cls._get_urls_by_quality(soup)

        for quality in cls._quality_order:
            if url := urls_by_quality.get(quality):
                return url

        return page_url

    @staticmethod
    def _get_urls_by_quality(soup: BeautifulSoup) -> dict[str, str]:
        urls_by_quality: dict[str, str] = {}
        for link in soup.select("#chooser_fullhd a.choose"):
            if not isinstance(link, Tag):
                continue

            href = link.get("href")
            if not isinstance(href, str):
                continue

            quality = link.text.strip().lower()
            if quality:
                urls_by_quality[quality] = href

        return urls_by_quality
