import re
from typing import Any

from services.http import HttpService

from ..exceptions import SerializationError
from ._base import BaseExtractor, ExtractedVideoData


class ApiExtractor(BaseExtractor):
    _expected_errors = (*BaseExtractor._expected_errors, SerializationError)

    def __init__(self, api_root: str) -> None:
        self.api_root = api_root

    async def _extract_video_data(self, url: str) -> ExtractedVideoData:
        request_url = f"{self.api_root}/api/hybrid/video_data?url={url}"
        data = await HttpService.get_json(request_url)
        return self._serialize_api_data(data)

    @staticmethod
    def _serialize_api_data(data: dict[str, Any]) -> ExtractedVideoData:
        try:
            api_data = data["data"]
            if not isinstance(api_data, dict):
                raise SerializationError

            video_url = ""
            images_urls: list[str] = []
            height = None
            width = None
            duration = None

            if "image_post_info" in api_data:
                for img in api_data["image_post_info"]["images"]:
                    images_urls.append(img["display_image"]["url_list"][0])
            if not images_urls and "video" in api_data:
                video_data = api_data["video"]
                video_url = video_data["play_addr"]["url_list"][0]
                height = video_data.get("height")
                width = video_data.get("width")
                duration = video_data.get("duration")
                if duration:
                    duration = duration // 1000

            music_url = api_data["music"]["play_url"]["url_list"][0]

            if re.search(r"\bmusic\b|\bmime_type=audio_mpeg\b", video_url):
                video_url = ""

            return {
                "video_url": video_url,
                "music_url": music_url,
                "images_urls": images_urls,
                "height": height,
                "width": width,
                "duration": duration,
            }
        except (AttributeError, IndexError, KeyError, TypeError, ValueError) as error:
            raise SerializationError from error
