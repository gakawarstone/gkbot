from services.gallery_dl import GalleryDlExtractionError, GalleryDlService

from ._base import BaseExtractor, ExtractedVideoData


class GalleryDl(BaseExtractor):
    _expected_errors = (*BaseExtractor._expected_errors, GalleryDlExtractionError)
    _normalize_url = True

    async def _extract_video_data(self, url: str) -> ExtractedVideoData:
        slideshow_info = await GalleryDlService.extract_slideshow_info(url)
        return {
            "music_url": slideshow_info.music_url,
            "images_urls": slideshow_info.images_urls,
            "height": slideshow_info.height,
            "width": slideshow_info.width,
            "duration": slideshow_info.duration,
        }
