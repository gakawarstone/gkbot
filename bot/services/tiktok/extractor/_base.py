from abc import ABC, abstractmethod

from ..types import InfoVideoTikTok


class BaseExtractor(ABC):
    @abstractmethod
    async def get_video_info(cls, url: str) -> InfoVideoTikTok:
        pass

    @abstractmethod
    async def get_video_file_url(cls, url: str) -> InfoVideoTikTok:
        pass
