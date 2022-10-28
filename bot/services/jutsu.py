from dataclasses import dataclass
from typing import TypeAlias
from aiogram.types import BufferedInputFile
from bs4 import BeautifulSoup, ResultSet, SoupStrainer

from .base_downloader import BaseDownloader

_Link: TypeAlias = str
_Pixel: TypeAlias = int


@dataclass
class _Source:
    resolution: _Pixel
    link: _Link


class InvalidUrl(Exception):
    "Jut.su invalid url"


class JutSuDownloader(BaseDownloader):
    @classmethod
    async def download_video(cls, url: str) -> BufferedInputFile:
        try:
            low_resolution_source = cls.__get_sources(url)[-1]
            file = await cls._download_file_from_url(
                low_resolution_source.link)
        except IndexError:
            raise InvalidUrl
        return BufferedInputFile(file, 'video.mp4')

    @classmethod
    def __get_sources(cls, url: str) -> list[_Source]:
        soup = cls._get_soup(url)
        return [
            cls.__format_source(elem)
            for elem in cls.__find_raw_sources(soup)
        ]

    @staticmethod
    def __find_raw_sources(soup: BeautifulSoup) -> ResultSet:
        return soup.find_all('video')[0].find_all('source')

    @staticmethod
    def __format_source(element: SoupStrainer) -> _Source:
        return _Source(
            resolution=int(element['label'][:-1]),
            link=element['src']
        )
