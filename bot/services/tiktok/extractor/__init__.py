from utils.async_for_first_success import async_for_first_success
from ..types import InfoVideoTikTok
from ..exceptions import TikTokInfoExtractionFailed
from .exceptions import SourceInfoExtractFailed
from .proxytok import ProxyTok
from .api import ApiExtractor
from .snaptik import Snaptik
from ._base import BaseExtractor


_EXTRACTORS: list[BaseExtractor] = [
    ProxyTok("https://proxitok.belloworld.it"),
    ApiExtractor("http://ttapi.gws.freemyip.com"),
    Snaptik(),
    ProxyTok("https://proxitok.pabloferreiro.es"),
    ProxyTok("https://tok.adminforge.de"),
    ApiExtractor("https://api.douyin.wtf"),
    ProxyTok("https://proxitok.esmailelbob.xyz"),
    ProxyTok("https://proxitok.pussthecat.org"),
    ProxyTok("https://cringe.whatever.social"),
    ProxyTok("https://tok.habedieeh.re"),
    ProxyTok("https://tok.artemislena.eu"),
    ProxyTok("https://tik.hostux.net"),
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
    async def get_video_url(cls, url: str, source: BaseExtractor) -> str:
        return await source.get_video_file_url(url)

    @classmethod
    @async_for_first_success_extractor
    async def get_video_info(cls, url: str, source: BaseExtractor) -> InfoVideoTikTok:
        return await source.get_video_info(url)
