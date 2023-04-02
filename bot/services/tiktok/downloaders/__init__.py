from .exceptions import SourceDownloadFailed
from .proxytok import ProxyTok
from .snaptik import SnaptikDownloader
from .api import ApiDownloader
from ._base import BaseDownloader
from typing import AsyncGenerator


_DOWNLOADERS: list[BaseDownloader] = [
    ApiDownloader(),
    ProxyTok('https://tt.vern.cc'),
    ProxyTok('https://tok.adminforge.de'),
    ProxyTok('https://proxitok.pabloferreiro.es'),
    SnaptikDownloader(),
    ProxyTok('https://proxitok.pussthecat.org'),
    ProxyTok('https://cringe.whatever.social'),
    ProxyTok('https://tok.habedieeh.re'),
    ProxyTok('https://proxitok.esmailelbob.xyz'),
    ProxyTok('https://tok.artemislena.eu'),
    ProxyTok('https://tik.hostux.net'),
    ProxyTok('https://proxitok.pufe.org'),
    ProxyTok('https://proxitok.lunar.icu'),
]


class DownloadersManager:
    @classmethod
    async def get_video_url_in_sources(cls, url: str) -> AsyncGenerator[str, None]:
        for source in _DOWNLOADERS:
            try:
                yield (await source.get_video_info(url)).video_url
            except SourceDownloadFailed:
                continue
