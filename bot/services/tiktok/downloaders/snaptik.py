from tiktok_downloader.snaptik import snaptik_async
from tiktok_downloader.Except import InvalidUrl

from ..exceptions import TikTokInvalidUrl
from ..types import InfoVideoTikTok
from ._base import BaseDownloader
from .exceptions import SourceDownloadFailed


class SnaptikDownloader(BaseDownloader):
    async def get_video_info(self, url: str) -> InfoVideoTikTok:
        try:
            response = InfoVideoTikTok(
                video_url=(await snaptik_async(url))[0].json,
                music_url=''
            )
            return response
        except InvalidUrl:
            raise TikTokInvalidUrl(url)
        except IndexError:
            raise SourceDownloadFailed(self)
