from services.gallery_dl import GalleryDlExtractionError, GalleryDlService
from services.http import HttpRequestError
from ..types import InfoVideoTikTok
from ._base import BaseExtractor
from .exceptions import SourceInfoExtractFailed


class GalleryDl(BaseExtractor):
    async def get_video_info(self, url: str) -> InfoVideoTikTok:
        try:
            full_url = await self._extract_full_url(url)
            slideshow_info = await GalleryDlService.extract_slideshow_info(full_url)
            return InfoVideoTikTok(
                video_url=None,
                video_input_file=None,
                music_url=slideshow_info.music_url,
                images_urls=slideshow_info.images_urls,
                height=slideshow_info.height,
                width=slideshow_info.width,
                duration=slideshow_info.duration,
            )
        except (GalleryDlExtractionError, HttpRequestError):
            raise SourceInfoExtractFailed(self)

    async def get_video_file_url(self, url: str) -> str:
        raise SourceInfoExtractFailed(self)
