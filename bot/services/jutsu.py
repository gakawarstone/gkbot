from dataclasses import dataclass
from typing import TypeAlias
from aiogram.types import BufferedInputFile
from bs4 import BeautifulSoup, Tag

from services.http import HttpService, HttpRequestError

_Link: TypeAlias = str
_Pixel: TypeAlias = int


@dataclass
class _Source:
    resolution: _Pixel
    link: _Link


class InvalidUrl(Exception):
    "Jut.su invalid url"


class JutSuDownloader:
    @classmethod
    async def download_video(cls, url: str) -> BufferedInputFile:
        try:
            video_url = (await cls.__get_sources(url))[-1].link
            file = await HttpService.get(video_url)
        except (IndexError, HttpRequestError):
            raise InvalidUrl
        return BufferedInputFile(file, "video.mp4")

    @classmethod
    async def __get_sources(cls, url: str) -> list[_Source]:
        soup = await cls.__get_soup(url)

        video_elements = soup.find_all("video")
        if not video_elements:
            return []

        video_element = video_elements[0]
        if not isinstance(video_element, Tag) or not hasattr(video_element, "find_all"):
            return []

        sources = video_element.find_all("source")
        valid_sources = []
        for elem in sources:
            if isinstance(elem, Tag) and elem.get("label") and elem.get("src"):
                valid_sources.append(cls.__format_source(elem))

        return valid_sources

    @staticmethod
    def __format_source(element: Tag) -> _Source:
        label = element.get("label")
        src = element.get("src")

        if not label or not src:
            raise ValueError("Missing required attributes")

        if isinstance(label, list):
            label = label[0] if label else ""

        if isinstance(src, list):
            src = src[0] if src else ""

        if not isinstance(label, str) or not isinstance(src, str):
            raise TypeError("Invalid attribute types")

        return _Source(resolution=int(label[:-1]), link=src)

    @staticmethod
    async def __get_soup(url: str) -> BeautifulSoup:
        return BeautifulSoup(await HttpService.get(url), "html.parser")
