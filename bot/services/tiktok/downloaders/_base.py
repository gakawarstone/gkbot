from abc import ABC, abstractmethod

from ..types import InfoVideoTikTok


class BaseDownloader(ABC):
    @abstractmethod
    async def get_video_info(self, url: str) -> InfoVideoTikTok:
        pass
