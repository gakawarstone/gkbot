# from urllib.parse import unquote
#
# from bs4 import BeautifulSoup
#
# from services.http import HttpService, HttpRequestError
from ..types import InfoVideoTikTok
from ._base import BaseExtractor
from .exceptions import SourceInfoExtractFailed


# NOTE: DEPRECATED: ProxyTok is not used anymore, but kept for reference
class ProxyTok(BaseExtractor):
    def __init__(self, url: str) -> None:
        self.__instance_url = url

    async def get_video_info(self, url: str) -> InfoVideoTikTok:
        raise SourceInfoExtractFailed(self)
        # try:
        #     return InfoVideoTikTok(
        #         video_url=await self.get_video_file_url(url),
        #         video_input_file=None,
        #         music_url=await self._get_music_url(url),
        #         images_urls=await self._find_images_urls(url),
        #     )
        # except (KeyError, IndexError, ValueError, HttpRequestError):
        #     raise SourceInfoExtractFailed(self)

    async def get_video_file_url(self, url: str) -> str:
        return ""
        # # return "https://955baff6cca70dc5effd971347c5fad6.serveo.net/TikTok%20video%20%237398864154213256454%20%5B7398864154213256454%5D.mp4"
        # url_in_proxytok = await self._get_url_in_proxytok(url)
        # print("proxy: ", url_in_proxytok)
        # video_file_url = await self._find_video_file_url(url_in_proxytok)
        # print("url: ", video_file_url)
        #
        # if not video_file_url:
        #     return ""
        # norm = self._normalize_link(video_file_url)
        # print(unquote(norm))
        # return unquote(norm)

    # async def _get_music_url(self, url: str) -> str:
    #     url_in_proxytok = await self._get_url_in_proxytok(url)
    #     soup = await self._get_soup(url_in_proxytok)
    #     if not (audio := soup.find("audio")):
    #         raise ValueError
    #     return self._normalize_link(audio["src"])
    #
    # async def _find_images_urls(self, url: str) -> list[str]:
    #     # FIXME: didnt work
    #     return []
    #     url_in_proxytok = await self._get_url_in_proxytok(url)
    #     soup = await self._get_soup(url_in_proxytok)
    #     return [
    #         self._extract_sublink(i.img["src"])
    #         for i in soup.find_all(class_="slides-item")
    #     ]
    #
    # async def _get_url_in_proxytok(self, url: str) -> str:
    #     if self._is_short_link(url):
    #         url = await self._extract_full_url(url)
    #     return self.__instance_url + "/@" + url.split("@")[-1]
    #
    # def _is_short_link(self, url: str) -> bool:
    #     return "@" not in url
    #
    # def _get_video_code(self, url: str) -> str:
    #     return url.split("/")[3]
    #
    # async def _find_video_file_url(self, url_in_proxytok: str) -> str:
    #     soup = await self._get_soup(url_in_proxytok)
    #
    #     sources = soup.find_all("source")
    #     if not sources:
    #         return ""
    #
    #     href = sources[0]["src"]
    #     if not self._is_link_valid(href):
    #         return ""
    #     return href
    #
    # async def _get_soup(self, url: str) -> BeautifulSoup:
    #     try:
    #         return BeautifulSoup(await HttpService.get(url), "html.parser")
    #     except HttpRequestError:
    #         raise SourceInfoExtractFailed(self)
    #
    # def _is_link_valid(self, url: str) -> bool:
    #     return url.startswith((self.__instance_url, "/stream"))
    #
    # def _extract_sublink(self, url: str) -> str:
    #     return unquote(url.split("?")[1][4:])
    #
    # def _normalize_link(self, url: str) -> str:
    #     if not self._is_link_relative(url):
    #         return url
    #     return self.__instance_url + url
    #
    # def _is_link_relative(self, url: str) -> bool:
    #     return not url.startswith("http")
