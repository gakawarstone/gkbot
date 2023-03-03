from abc import ABC, abstractmethod

import aiohttp
from bs4 import BeautifulSoup

from ..types import InfoVideoTikTok


_headers = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        'AppleWebKit/537.36 (KHTML, like Gecko)'
        'Chrome/106.0.0.0 Safari/537.36'
    )
}


class BaseDownloader(ABC):
    @abstractmethod
    async def get_video_info(cls, url: str) -> InfoVideoTikTok:
        pass

    async def _get_soup(self, url: str) -> BeautifulSoup:
        return BeautifulSoup(await self._get_html(url), 'html.parser')

    async def _get_html(self, url: str) -> bytes:
        async with aiohttp.ClientSession(conn_timeout=None) as session:
            async with session.get(url, headers=_headers) as response:
                return await response.content.read()
