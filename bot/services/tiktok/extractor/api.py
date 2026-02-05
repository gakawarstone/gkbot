import re

from services.http import HttpService, HttpRequestError
from ..types import InfoVideoTikTok
from ..exceptions import SerializationError
from ._base import BaseExtractor
from .exceptions import SourceInfoExtractFailed


class ApiExtractor(BaseExtractor):
    def __init__(self, api_root: str) -> None:
        self.api_root = api_root

    async def get_video_info(self, url: str) -> InfoVideoTikTok:
        try:
            request_url = f"{self.api_root}/api/hybrid/video_data?url={url}"
            data = await HttpService.get_json(request_url)
            return self._serialize_api_data(data)
        except (HttpRequestError, SerializationError):
            raise SourceInfoExtractFailed(self)

    async def get_video_file_url(self, url: str) -> str:
        video_info = await self.get_video_info(url)

        if video_info.video_url is None:
            raise ValueError("Video URL is None")

        return video_info.video_url

    @staticmethod
    def _serialize_api_data(data: dict) -> InfoVideoTikTok:
        try:
            video_url = ""
            images_urls = []
            height = None
            width = None
            duration = None

            if "image_post_info" in data["data"]:
                for img in data["data"]["image_post_info"]["images"]:
                    images_urls.append(img["display_image"]["url_list"][0])
            if "video" in data["data"]:
                video_data = data["data"]["video"]
                video_url = video_data["play_addr"]["url_list"][0]
                height = video_data.get("height")
                width = video_data.get("width")
                duration = video_data.get("duration")
                if duration:
                    duration = duration // 1000

            music_url = data["data"]["music"]["play_url"]["url_list"][0]

            if re.search(r"\bmusic\b|\bmime_type=audio_mpeg\b", video_url):
                video_url = ""

            return InfoVideoTikTok(
                video_url=video_url,
                video_input_file=None,
                music_url=music_url,
                images_urls=images_urls,
                height=height,
                width=width,
                duration=duration,
            )
        except (KeyError, ValueError):
            raise SerializationError
