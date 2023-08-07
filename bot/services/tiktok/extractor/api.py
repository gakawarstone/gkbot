import aiohttp
from aiohttp.client_exceptions import ContentTypeError

from ..types import InfoVideoTikTok
from ..exceptions import SerializationError
from ._base import BaseExtractor
from .exceptions import SourceInfoExtractFailed


class ApiExtractor(BaseExtractor):
    async def get_video_info(self, url: str) -> InfoVideoTikTok:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'https://api.douyin.wtf/api?url={url}'
                ) as response:
                    return self._serialize_api_data(
                        await response.json()
                    )
        except (ContentTypeError, SerializationError):
            raise SourceInfoExtractFailed(self)

    @staticmethod
    def _serialize_api_data(data: dict) -> InfoVideoTikTok:
        try:
            video_url = ''
            images_urls = []

            if 'video_data' in data:
                video_url = data['video_data']['nwm_video_url']
            elif 'image_data' in data:
                images_urls = data['image_data']['no_watermark_image_list']
            else:
                raise ValueError

            return InfoVideoTikTok(
                video_url=video_url,
                music_url=data['music']['play_url']['uri'],
                images_urls=images_urls
            )
        except (KeyError, ValueError):
            raise SerializationError
