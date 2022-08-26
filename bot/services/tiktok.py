from dataclasses import dataclass

import aiohttp
from aiohttp.client_exceptions import ContentTypeError
from tiktok_downloader.snaptik import snaptik_async
from tiktok_downloader.Except import InvalidUrl

from aiogram.types import BufferedInputFile


@dataclass
class InfoVideoTikTok:
    video_url: str
    music_url: str


def info_video_tiktok_serializer(data: dict) -> InfoVideoTikTok:
    return InfoVideoTikTok(
        video_url=data['nwm_video_url'],
        music_url=data['video_music_url']
    )


class TikTokInvalidUrl(Exception):
    def __init__(self, url: str) -> None:
        self.url = url

    def __str__(self) -> str:
        return f'Invalid TikTok video url {self.url}'


class TikTokDownloader:
    @staticmethod
    async def __download_file_from_url(url: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.content.read()

    @classmethod
    async def __get_video_info_from_snaptik(cls, url: str) -> InfoVideoTikTok:
        try:
            return InfoVideoTikTok(
                video_url=(await snaptik_async(url))[0].json,
                music_url=''
            )
        except InvalidUrl:
            raise TikTokInvalidUrl(url)

    @classmethod
    async def __get_video_info(cls, url: str) -> InfoVideoTikTok:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'https://api.douyin.wtf/api?url={url}'
                ) as response:
                    return info_video_tiktok_serializer(
                        await response.json()
                    )
        except ContentTypeError:
            return await cls.__get_video_info_from_snaptik(url)
        except KeyError:
            raise TikTokInvalidUrl(url)

    @classmethod
    async def get_video_url(cls, url: str) -> str:
        return (await cls.__get_video_info(url)).video_url

    @classmethod
    async def get_video_as_input_file(cls, url: str) -> BufferedInputFile:
        return BufferedInputFile(
            file=await cls.__download_file_from_url(
                url=await cls.get_video_url(url)
            ),
            filename='video.mp4'
        )
