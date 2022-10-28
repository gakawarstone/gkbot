import aiohttp
import requests
from bs4 import BeautifulSoup

_headers = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        'AppleWebKit/537.36 (KHTML, like Gecko)'
        'Chrome/106.0.0.0 Safari/537.36'
    )
}


class BaseDownloader:
    @staticmethod
    def _get_soup(url: str) -> BeautifulSoup:
        html = requests.get(url, headers=_headers).content  # FIXME async
        return BeautifulSoup(html, 'html.parser')

    @staticmethod  # FIXME tt dl used func like this
    async def _download_file_from_url(url: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=_headers) as response:
                return await response.content.read()
