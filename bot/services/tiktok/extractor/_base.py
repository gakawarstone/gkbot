from abc import ABC, abstractmethod

from services.http import HttpService
from ..types import InfoVideoTikTok


class BaseExtractor(ABC):
    @abstractmethod
    async def get_video_info(self, url: str) -> InfoVideoTikTok:
        pass

    @abstractmethod
    async def get_video_file_url(self, url: str) -> str:
        pass

    async def _extract_full_url(self, url: str) -> str:
        redirected_url = await HttpService.get_redirected_url(url)
        return redirected_url.split("?")[0].replace("photo", "video")
