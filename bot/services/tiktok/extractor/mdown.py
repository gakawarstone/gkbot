from bs4 import BeautifulSoup
from bs4.element import Tag

import requests

from utils.async_wrapper import async_wrap
from ..types import InfoVideoTikTok
from .exceptions import SourceInfoExtractFailed
from ._base import BaseExtractor


class Mdown(BaseExtractor, requests.Session):
    _base_url = "https://musicaldown.com/"
    _headers = {
        "origin": "https://musicaldown.com",
        "referer": "https://musicaldown.com/en/",
        "sec-ch-ua": '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Linux",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    }

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
            return (await async_wrap(self._get_video_links)(url))[0]
        except (IndexError, ValueError):
            raise SourceInfoExtractFailed(self)

    def _get_video_links(self, url: str) -> list[str]:
        html = self.get(self._base_url).text

        soup = BeautifulSoup(html, "html.parser")
        form = {}
        for i in soup.find_all("input", attrs={"type": "hidden"}):
            if isinstance(i, Tag) and i.get("name") and i.get("value"):
                form[i["name"]] = i["value"]

        text_input = soup.find("input", attrs={"type": "text"})
        if isinstance(text_input, Tag) and text_input.get("name"):
            form[text_input["name"]] = url

        res = self.post(
            f"{self._base_url}download",
            data=form,
            headers=self._headers,
        )

        if "err" in res.url:
            raise ValueError

        links = []
        for link in BeautifulSoup(res.text, "html.parser").find_all(
            "a", attrs={"target": "_blank"}
        ):
            if isinstance(link, Tag) and link.get("href"):
                links.append(str(link["href"]))

        return links
