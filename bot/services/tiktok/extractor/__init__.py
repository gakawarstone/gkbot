from ..types import InfoVideoTikTok
from .exceptions import SourceInfoExtractFailed
from .proxytok import ProxyTok
# from .snaptik import SnaptikDownloader
from .api import ApiExtractor
from ._base import BaseExtractor


_EXTRACTORS: list[BaseExtractor] = [
    ProxyTok('https://proxitok.pabloferreiro.es'),
    ApiExtractor(),
    ProxyTok('https://tok.adminforge.de'),
    ProxyTok('https://tt.vern.cc'),
    # SnaptikDownloader(),  # NOTE: not working
    ProxyTok('https://proxitok.pussthecat.org'),
    ProxyTok('https://cringe.whatever.social'),
    ProxyTok('https://tok.habedieeh.re'),
    ProxyTok('https://proxitok.esmailelbob.xyz'),
    ProxyTok('https://tok.artemislena.eu'),
    ProxyTok('https://tik.hostux.net'),
    ProxyTok('https://proxitok.pufe.org'),
    ProxyTok('https://proxitok.lunar.icu'),
]


class TikTokInfoExtractor:
    @classmethod
    async def get_video_url(cls, url: str) -> str:
        return (await cls.get_video_info(url)).video_url

    @classmethod
    async def get_video_info(cls, url: str) -> InfoVideoTikTok:
        for source in _EXTRACTORS:
            try:
                return await source.get_video_info(url)
            except SourceInfoExtractFailed:
                continue
