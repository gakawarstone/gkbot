import re

import requests

from utils.async_wrapper import async_wrap

from ._base import BaseExtractor, VideoUrlExtractor


class TTDownloader(VideoUrlExtractor, requests.Session):
    _expected_errors = (*BaseExtractor._expected_errors, requests.RequestException)
    _normalize_url = True
    _base_url = "https://ttdownloader.com/"

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
