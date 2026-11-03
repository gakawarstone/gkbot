import re

import requests

from services.http import HttpRequestError, HttpService
from utils.async_wrapper import async_wrap

from ..types import InfoVideoTikTok
from ._base import BaseExtractor
from .exceptions import SourceInfoExtractFailed


class TTDownloader(BaseExtractor, requests.Session):
    _base_url = "https://ttdownloader.com/"

    async def get_video_info(self, url: str) -> InfoVideoTikTok:
        try:
            response = InfoVideoTikTok(
                video_url=await self.get_video_file_url(url),
                video_input_file=None,
                music_url="",
                images_urls=[],
            )
            return response
        except (IndexError, ValueError):
            raise SourceInfoExtractFailed(self)

    async def get_video_file_url(self, url: str) -> str:
        try:
            full_url = (await HttpService.get_redirected_url(url)).split("?")[0]
            # TTDownloader returns the soundtrack for photo posts.
            if "/photo/" in full_url:
                raise SourceInfoExtractFailed(self)
            links = await self._get_video_links(full_url)
            return links[0]
        except (HttpRequestError, IndexError, ValueError):
            raise SourceInfoExtractFailed(self)

    async def _get_video_links(self, url: str) -> list[str]:
        return await async_wrap(self.__get_video_links_sync)(url)

    def __get_video_links_sync(self, url: str) -> list[str]:
        html = self.get(self._base_url).text
        token = re.findall(r"value=\"([0-9a-z]+)\"", html)
        result = self.post(
            self._base_url + "search/",
            data={"url": url, "format": "", "token": token[0]},
        )
        nowm, wm, audio = re.findall(r"(https?://.*?.php\?v\=.*?)\"", result.text)
        return [nowm, wm, audio]
