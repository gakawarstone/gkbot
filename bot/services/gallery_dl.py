from dataclasses import dataclass
from typing import Any

from gallery_dl.exception import GalleryDLException, NoExtractorError
from gallery_dl.job import DataJob

from utils.async_wrapper import async_wrap


@dataclass
class GalleryDlSlideshowInfo:
    images_urls: list[str]
    music_url: str
    height: int | None = None
    width: int | None = None
    duration: int | None = None


class GalleryDlExtractionError(Exception):
    pass


class GalleryDlService:
    _url_message = 3

    @classmethod
    async def extract_slideshow_info(cls, url: str) -> GalleryDlSlideshowInfo:
        try:
            data = await cls._extract_json_data(url)
            return cls._serialize_slideshow_data(data)
        except (GalleryDLException, NoExtractorError, ValueError) as error:
            raise GalleryDlExtractionError from error

    @classmethod
    async def _extract_json_data(cls, url: str) -> list[Any]:
        job = DataJob(url, file=None)
        status = await async_wrap(job.run)()
        if status or getattr(job, "exception", None):
            raise ValueError("gallery-dl failed to extract data")
        return job.data

    @classmethod
    def _serialize_slideshow_data(cls, data: list[Any]) -> GalleryDlSlideshowInfo:
        images_urls: list[str] = []
        music_url = ""
        width = None
        height = None

        for item in data:
            if not isinstance(item, (list, tuple)) or len(item) < 3:
                continue

            message, media_url, metadata = item[:3]
            if message != cls._url_message or not isinstance(metadata, dict):
                continue

            if metadata.get("type") == "image":
                images_urls.append(media_url)
                width = width or metadata.get("width")
                height = height or metadata.get("height")
            elif metadata.get("type") == "audio":
                music_url = media_url

        if not images_urls:
            raise ValueError("gallery-dl did not extract slideshow images")

        return GalleryDlSlideshowInfo(
            images_urls=images_urls,
            music_url=music_url,
            height=height,
            width=width,
        )
