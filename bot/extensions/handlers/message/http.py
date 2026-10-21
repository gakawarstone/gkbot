from bs4 import BeautifulSoup

from services.http import HttpService


class HttpExtension:
    async def _get_soup(
        self,
        url: str,
        headers: dict[str, str] | None = HttpService.headers,
    ) -> BeautifulSoup:
        html = await HttpService.get(url, headers=headers)
        return BeautifulSoup(html, "html.parser")
