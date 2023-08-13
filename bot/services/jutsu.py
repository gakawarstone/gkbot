from dataclasses import dataclass
from typing import TypeAlias
from aiogram.types import BufferedInputFile
from bs4 import BeautifulSoup, SoupStrainer

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
        return BufferedInputFile(file, 'video.mp4')

    @classmethod
    async def __get_sources(cls, url: str) -> list[_Source]:
        soup = await cls.__get_soup(url)
        return [
            cls.__format_source(elem)
            for elem in soup.find_all('video')[0].find_all('source')
        ]

    @staticmethod
    def __format_source(element: SoupStrainer) -> _Source:
        return _Source(
            resolution=int(element['label'][:-1]),
            link=element['src']
        )

    @staticmethod
    async def __get_soup(url: str) -> BeautifulSoup:
        return BeautifulSoup(await HttpService.get(url), 'html.parser')
