from utils.async_for_first_success import async_for_first_success

from ..exceptions import TikTokInfoExtractionFailed
from ..types import InfoVideoTikTok
from ._base import BaseExtractor
from .api import ApiExtractor
from .exceptions import SourceInfoExtractFailed
from .gallery_dl import GalleryDl
from .mdown import Mdown
from .snaptik import Snaptik
from .tikdown import Tikdown
from .tikwm import TikWm
from .ttdownloader import TTDownloader
from .yt_dlp import YtDlp

_EXTRACTORS: list[BaseExtractor] = [
    YtDlp(),
    ApiExtractor("https://api.douyin.wtf"),
    GalleryDl(),
    TikWm(),
    TTDownloader(),
    ApiExtractor("http://ttapi.gws.freemyip.com"),
    Snaptik(),
    Mdown(),
    Tikdown(),
]


class TikTokInfoExtractor:
    async_for_first_success_extractor = async_for_first_success(
        sources=_EXTRACTORS,
        inject_as="source",
        exception_to_continue=SourceInfoExtractFailed,
        exception_if_all_failed=TikTokInfoExtractionFailed,
        exception_if_all_failed_inject_args=[1],
    )

    @classmethod
    @async_for_first_success_extractor
    async def get_video_url(
        cls, url: str, source: BaseExtractor = _EXTRACTORS[0]
    ) -> str:
        return await source.get_video_file_url(url)

    @classmethod
    @async_for_first_success_extractor
    async def get_video_info(
        cls, url: str, source: BaseExtractor = _EXTRACTORS[0]
    ) -> InfoVideoTikTok:
        return await source.get_video_info(url)
