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
        return (await self.get_video_info(url)).video_url

    @staticmethod
    def _serialize_api_data(data: dict) -> InfoVideoTikTok:
        try:
            video_url = ""
            images_urls = []

            if "image_post_info" in data["data"]:
                for img in data["data"]["image_post_info"]["images"]:
                    images_urls.append(img["display_image"]["url_list"][0])
            if "downloadAddr" in data["data"]["video"]:
                video_url = ""
                # FIXME: not works
                # video_url = data["data"]["video"]["downloadAddr"]

            music_url = data["data"]["music"]["play_url"]["url_list"][0]

            return InfoVideoTikTok(
                video_url=video_url,
                music_url=music_url,
                images_urls=images_urls,
            )
        except (KeyError, ValueError):
            raise SerializationError
