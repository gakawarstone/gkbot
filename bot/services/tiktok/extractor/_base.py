from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from typing import ClassVar, TypedDict
from urllib.parse import urlsplit, urlunsplit

from aiogram.types import InputFile
from aiohttp import ClientError

from services.http import HttpRequestError, HttpService

from ..types import InfoVideoTikTok
from .exceptions import SourceInfoExtractFailed


class ExtractedVideoData(TypedDict, total=False):
    """Provider data. Omitted fields receive defaults in BaseExtractor."""

    video_url: str | None
    video_input_file: InputFile | None
    music_url: str | None
    images_urls: list[str] | None
    height: int | None
    width: int | None
    duration: int | None


class BaseExtractor(ABC):
    _expected_errors: ClassVar[tuple[type[Exception], ...]] = (
        HttpRequestError,
        ClientError,
        TimeoutError,
        IndexError,
        KeyError,
        TypeError,
        ValueError,
    )
    _normalize_url: ClassVar[bool] = False
    _supports_photo_posts: ClassVar[bool] = True

    async def get_video_info(self, url: str) -> InfoVideoTikTok:
        """Build shared defaults and expose expected failures to the fallback."""
        with self._translate_errors():
            if self._normalize_url:
                url = await self._extract_full_url(url)
            data = await self._extract_video_data(url)
            return InfoVideoTikTok(
                video_url=data.get("video_url"),
                video_input_file=data.get("video_input_file"),
                music_url=data.get("music_url", ""),
                images_urls=data.get("images_urls", []),
                height=data.get("height"),
                width=data.get("width"),
                duration=data.get("duration"),
            )

    @abstractmethod
    async def _extract_video_data(self, url: str) -> ExtractedVideoData:
        """Obtain provider data; leave defaults and exception translation here."""

    async def get_video_file_url(self, url: str) -> str:
        """Compatibility entry point for callers that require a public URL.

        File-only and slideshow providers fail through the same contract so
        callers can continue to another provider.
        """
        with self._translate_errors():
            return await self._extract_video_file_url(url)

    async def _extract_video_file_url(self, url: str) -> str:
        info = await self.get_video_info(url)
        if not info.video_url:
            raise ValueError("Provider did not return a public video URL")
        return info.video_url

    @contextmanager
    def _translate_errors(self) -> Iterator[None]:
        try:
            yield
        except self._expected_errors as error:
            raise SourceInfoExtractFailed(self) from error

    async def _extract_full_url(self, url: str) -> str:
        """Resolve short links and normalize TikTok's photo resource path."""
        redirected_url = urlsplit(await HttpService.get_redirected_url(url))
        if not self._supports_photo_posts and "/photo/" in redirected_url.path:
            raise ValueError("Provider returns only audio for photo posts")
        path = redirected_url.path.replace("/photo/", "/video/", 1)
        return urlunsplit(redirected_url._replace(path=path, query="", fragment=""))


class VideoUrlExtractor(BaseExtractor):
    async def _extract_video_data(self, url: str) -> ExtractedVideoData:
        video_url = (await self._get_video_links(url))[0]
        if not video_url:
            raise ValueError("Provider returned an empty video URL")
        return {"video_url": video_url}

    @abstractmethod
    async def _get_video_links(self, url: str) -> list[str]:
        """Return provider media links with the preferred video first."""
