from bs4 import BeautifulSoup

from services.http import HttpService


class HttpExtension:
    async def _get_soup(self, url: str) -> BeautifulSoup:
        html = await HttpService.get(url)
        return BeautifulSoup(html, "html.parser")
