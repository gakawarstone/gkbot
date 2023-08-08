from urllib.parse import unquote

from aiohttp import ClientConnectionError

from ..types import InfoVideoTikTok
from ._base import BaseExtractor
from .exceptions import SourceInfoExtractFailed


class ProxyTok(BaseExtractor):
    def __init__(self, url: str) -> None:
        self.__instance_url = url

    async def get_video_info(self, url: str) -> InfoVideoTikTok:
        try:
            return InfoVideoTikTok(
                video_url=await self._get_video_file_url(url),
                music_url=await self._get_music_url(url),
                images_urls=await self._find_images_urls(url)
            )
        except (KeyError, IndexError, ValueError, ClientConnectionError):
            raise SourceInfoExtractFailed(self)

    async def _get_video_file_url(self, url: str) -> str:
        url_in_proxytok = self._get_url_in_proxytok(url)
        video_file_url = await self._find_video_file_url(url_in_proxytok)

        if not video_file_url:
            return ''
        if not self._is_link_relative(video_file_url):
            return video_file_url
        return self.__instance_url + video_file_url

    async def _get_music_url(self, url: str) -> str:
        url_in_proxytok = self._get_url_in_proxytok(url)
        soup = await self._get_soup(url_in_proxytok)
        if not (audio := soup.find('audio')):
            raise ValueError
        return self.__instance_url + audio['src']

    async def _find_images_urls(self, url: str) -> list[str]:
        url_in_proxytok = self._get_url_in_proxytok(url)
        soup = await self._get_soup(url_in_proxytok)
        return [unquote(i.img['src'].split('?')[1][4:])
                for i in soup.find_all(class_='slides-item')]

    def _get_url_in_proxytok(self, url: str) -> str:
        if not self._is_short_link(url):
            return self.__instance_url + '/@' + url.split('@')[-1]
        return self.__instance_url + '/t/' + self._get_video_code(url)

    def _is_short_link(self, url: str) -> bool:
        return not '@' in url

    def _get_video_code(self, url: str) -> str:
        return url.split('/')[-2]

    async def _find_video_file_url(self, url_in_proxytok: str) -> str:
        soup = await self._get_soup(url_in_proxytok)

        buttons = soup.find_all(class_='is-success')
        if len(buttons) < 2:
            return ''

        href = buttons[-1]['href']
        if not self._is_link_valid(href):
            return ''
        return href

    def _is_link_valid(self, url: str) -> bool:
        return url.startswith((self.__instance_url, '/download'))

    def _is_link_relative(self, url: str) -> bool:
        return not url.startswith('http')
