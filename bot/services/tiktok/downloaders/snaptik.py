from tiktok_downloader.snaptik import snaptik_async
from tiktok_downloader.Except import InvalidUrl

from ..exceptions import TikTokInvalidUrl
from ..types import InfoVideoTikTok

from pprint import pprint


class SnaptikDownloadFailed(Exception):
    pass


class SnaptikDownloader:
    @classmethod
    async def get_video_info(cls, url: str) -> InfoVideoTikTok:
        try:
            pprint(await snaptik_async(url))

            response = InfoVideoTikTok(
                video_url=(await snaptik_async(url))[0].json,
                music_url=''
            )
            return response
        except InvalidUrl:
            raise TikTokInvalidUrl(url)
        except IndexError:
            raise SnaptikDownloadFailed
