from typing import Any
from urllib.parse import urlencode, urljoin

from services.http import HttpRequestError, HttpService

from ..exceptions import SerializationError
from ..types import InfoVideoTikTok
from ._base import BaseExtractor
from .exceptions import SourceInfoExtractFailed


class TikWm(BaseExtractor):
    _base_url = "https://www.tikwm.com"

    async def get_video_info(self, url: str) -> InfoVideoTikTok:
        try:
            query = urlencode({"url": url})
            data = await HttpService.get_json(f"{self._base_url}/api/?{query}")
            return self._serialize_api_data(data)
        except (HttpRequestError, SerializationError) as error:
            raise SourceInfoExtractFailed(self) from error

    async def get_video_file_url(self, url: str) -> str:
        info = await self.get_video_info(url)
        if not info.video_url:
            raise SourceInfoExtractFailed(self)
        return info.video_url

    @classmethod
    def _serialize_api_data(cls, data: dict[str, Any]) -> InfoVideoTikTok:
        try:
            if data["code"] != 0 or not isinstance(data["data"], dict):
                raise SerializationError
            post = data["data"]
            images = post.get("images") or []
            if not isinstance(images, list) or any(
                not isinstance(image, str) or not image for image in images
            ):
                raise SerializationError

            # Photo posts also have a play URL, but it contains only audio.
            video_url = None if images else urljoin(cls._base_url, post["play"])
            if not images and not post["play"]:
                raise SerializationError
            music_url = (post.get("music_info") or {}).get("play") or post.get("music")
            return InfoVideoTikTok(
                video_url=video_url,
                video_input_file=None,
                music_url=urljoin(cls._base_url, music_url) if music_url else None,
                images_urls=[urljoin(cls._base_url, image) for image in images],
                duration=None if images else post.get("duration"),
            )
        except (AttributeError, KeyError, TypeError, ValueError) as error:
            raise SerializationError from error
