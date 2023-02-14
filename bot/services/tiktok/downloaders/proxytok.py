from ._base import BaseDownloader
from ..types import InfoVideoTikTok


class ProxyTok(BaseDownloader):
    __base_url = 'https://tt.vern.cc/download?url='

    @classmethod
    async def get_video_info(cls, url: str) -> InfoVideoTikTok:
        return InfoVideoTikTok(
            video_url=cls.__base_url + url,
            music_url='deprecated'
        )
