import aiohttp
from aiogram.types import BufferedInputFile

from .exceptions import TikTokDownloadFailed
from .downloaders import DownloadersManager


class TikTokDownloader:
    @classmethod
    async def get_video_url(cls, url: str) -> str:
        async for video_url in DownloadersManager.get_video_url_in_sources(url):
            return video_url
        raise TikTokDownloadFailed(url)

    @classmethod
    async def get_video_as_input_file(cls, url: str) -> BufferedInputFile:
        return BufferedInputFile(
            file=await cls.__get_video_file(url),
            filename='video.mp4'
        )

    @classmethod
    async def __get_video_file(cls, url: str) -> bytes:
        async for video_url in DownloadersManager.get_video_url_in_sources(url):
            return await cls.__download_file_from_url(video_url)
        raise TikTokDownloadFailed(url)

    @staticmethod
    async def __download_file_from_url(url: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.content.read()
