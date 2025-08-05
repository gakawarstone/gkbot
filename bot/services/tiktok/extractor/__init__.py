from utils.async_for_first_success import async_for_first_success
from ..types import InfoVideoTikTok
from ..exceptions import TikTokInfoExtractionFailed
from ._base import BaseExtractor
from .exceptions import SourceInfoExtractFailed

# from .proxytok import ProxyTok
from .api import ApiExtractor
from .snaptik import Snaptik
from .mdown import Mdown
from .tikdown import Tikdown
from .ttdownloader import TTDownloader
from .yt_dlp import YtDlp


_EXTRACTORS: list[BaseExtractor] = [
    YtDlp(),
    ApiExtractor("https://api.douyin.wtf"),
    # ProxyTok("https://proxitok.pabloferreiro.es"),
    TTDownloader(),
    # ProxyTok("https://tok.habedieeh.re"),
    # ProxyTok("https://proxitok.belloworld.it"),
    # ProxyTok("https://tt.vern.cc"),
    ApiExtractor("http://ttapi.gws.freemyip.com"),
    # ProxyTok("http://tt.gws.freemyip.com"),
    Snaptik(),
    Mdown(),
    Tikdown(),
    # ProxyTok("https://tok.adminforge.de"),
    # ProxyTok("https://proxitok.esmailelbob.xyz"),
    # ProxyTok("https://proxitok.pussthecat.org"),
    # ProxyTok("https://cringe.whatever.social"),
    # ProxyTok("https://tok.artemislena.eu"),
    # ProxyTok("https://tik.hostux.net"),
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
    async def get_video_url(cls, url: str, source: BaseExtractor = YtDlp()) -> str:
        return await source.get_video_file_url(url)

    @classmethod
    @async_for_first_success_extractor
    async def get_video_info(
        cls, url: str, source: BaseExtractor = YtDlp()
    ) -> InfoVideoTikTok:
        return await source.get_video_info(url)
