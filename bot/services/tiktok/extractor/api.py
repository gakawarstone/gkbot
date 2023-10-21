from services.http import HttpService, HttpRequestError
from ..types import InfoVideoTikTok
from ..exceptions import SerializationError
from ._base import BaseExtractor
from .exceptions import SourceInfoExtractFailed


class ApiExtractor(BaseExtractor):
    async def get_video_info(self, url: str) -> InfoVideoTikTok:
        try:
            request_url = f"https://api.douyin.wtf/api?url={url}"
            data = await HttpService.get_json(request_url)
            return self._serialize_api_data(data)
        except (HttpRequestError, SerializationError):
            raise SourceInfoExtractFailed(self)

    async def get_video_file_url(self, url: str) -> str:
        return (await self.get_video_info(url)).video_url

    @staticmethod
    def _serialize_api_data(data: dict) -> InfoVideoTikTok:
        try:
            video_url = ""
            images_urls = []

            if "video_data" in data:
                video_url = data["video_data"]["nwm_video_url"]
            elif "image_data" in data:
                images_urls = data["image_data"]["no_watermark_image_list"]
            else:
                raise ValueError

            return InfoVideoTikTok(
                video_url=video_url,
                music_url=data["music"]["play_url"]["uri"],
                images_urls=images_urls,
            )
        except (KeyError, ValueError):
            raise SerializationError
