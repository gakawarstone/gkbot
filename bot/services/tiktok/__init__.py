import aiohttp
from aiogram.types import BufferedInputFile

from .exceptions import TikTokDownloadFailed
from .downloaders.proxytok import ProxyTok
from .downloaders.api import ApiDownloader, ApiDownloadFailed
from .downloaders.snaptik import SnaptikDownloader, SnaptikDownloadFailed


class TikTokDownloader:
    @classmethod
    async def get_video_url(cls, url: str) -> str:
        return (await ProxyTok.get_video_info(url)).video_url

    @classmethod
    async def get_video_as_input_file(cls, url: str) -> BufferedInputFile:
        return BufferedInputFile(
            file=await cls.__get_video_file(url),
            filename='video.mp4'
        )

    @staticmethod
    async def __download_file_from_url(url: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.content.read()

    @classmethod
    async def __get_video_file(cls, url: str) -> bytes:
        try:
            video_url = (await ApiDownloader.get_video_info(url)).video_url
        except ApiDownloadFailed:
            video_url = (await SnaptikDownloader.get_video_info(url)).video_url
        except SnaptikDownloadFailed:
            raise TikTokDownloadFailed

        return await cls.__download_file_from_url(video_url)
