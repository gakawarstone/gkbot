import aiohttp
from aiohttp.client_exceptions import ContentTypeError

from ..types import InfoVideoTikTok
from ..serializers import info_video_tiktok_serializer
from ..exceptions import SerializationError
from ._base import BaseDownloader


class ApiDownloadFailed(Exception):
    pass


class ApiDownloader(BaseDownloader):
    @classmethod
    async def get_video_info(cls, url: str) -> InfoVideoTikTok:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'https://api.douyin.wtf/api?url={url}'
                ) as response:
                    return info_video_tiktok_serializer(
                        await response.json()
                    )
        except (ContentTypeError, SerializationError):
            raise ApiDownloadFailed
