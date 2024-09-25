import re

import requests

from utils.async_wrapper import async_wrap
from ..types import InfoVideoTikTok
from .exceptions import SourceInfoExtractFailed
from ._base import BaseExtractor


class TTDownloader(BaseExtractor, requests.Session):
    _base_url = "https://ttdownloader.com/"

    async def get_video_info(self, url: str) -> InfoVideoTikTok:
        try:
            full_url = await self._extract_full_url(url)
            response = InfoVideoTikTok(
                video_url=await self.get_video_file_url(full_url),
                music_url="",
                images_urls=[],
            )
            return response
        except (IndexError, ValueError):
            raise SourceInfoExtractFailed(self)

    async def get_video_file_url(self, url: str) -> str:
        try:
            return (await self._get_video_links(url))[0]
        except (IndexError, ValueError):
            raise SourceInfoExtractFailed(self)

    @async_wrap
    def _get_video_links(self, url: str) -> list[str]:
        html = self.get(self._base_url).text
        token = re.findall(r"value=\"([0-9a-z]+)\"", html)
        result = self.post(
            self._base_url + "search/",
            data={"url": url, "format": "", "token": token[0]},
        )
        nowm, wm, audio = re.findall(r"(https?://.*?.php\?v\=.*?)\"", result.text)
        return [nowm, wm, audio]
