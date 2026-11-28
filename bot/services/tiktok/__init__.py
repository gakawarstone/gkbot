import asyncio
from pathlib import Path
from subprocess import SubprocessError

from services.cache_dir import CacheDir, ReadProtectedCacheDir
from services.http import HttpService
from services.slideshow import SlideshowRenderer
from services.video_metadata import VideoMetadataService
from utils.async_cleanup import wait_for_completion

from .exceptions import TikTokInfoExtractionFailed, TikTokVideoUrlExtractionFailed
from .extractor import TikTokInfoExtractor
from .types import InfoVideoTikTok, TikTokVideo


class _TikTokCacheDir(ReadProtectedCacheDir):
    """Cache directory for TikTok fallback and previously pickled callbacks."""


class TikTokService:
    @classmethod
    async def get_video_url(cls, url: str) -> str:
        if video_url := await TikTokInfoExtractor.get_video_url(url):
            return video_url
        raise TikTokVideoUrlExtractionFailed(url)

    @classmethod
    async def get_video(cls, url: str) -> TikTokVideo:
        if not (info := await TikTokInfoExtractor.get_video_info(url)):
            raise TikTokInfoExtractionFailed(url)

        if info.video_file is None:
            info.video_file = await cls.__create_cached_video(info)

        await cls.__fill_missing_video_metadata(info)

        return TikTokVideo(
            url=info.video_url,
            file=info.video_file,
            height=info.height,
            width=info.width,
            duration=info.duration,
        )

    @classmethod
    async def __fill_missing_video_metadata(cls, info: InfoVideoTikTok) -> None:
        if info.height and info.width and info.duration:
            return

        is_generated_slideshow = bool(info.images_urls and not info.video_url)
        if is_generated_slideshow:
            info.height = SlideshowRenderer.SLIDESHOW_HEIGHT
            info.width = SlideshowRenderer.SLIDESHOW_WIDTH

        if not isinstance(info.video_file, Path):
            return
        try:
            metadata = await VideoMetadataService.get_video_metadata(
                str(info.video_file)
            )
        except SubprocessError:
            return

        if not info.height:
            info.height = metadata.get("height")
        if not info.width:
            info.width = metadata.get("width")
        if not info.duration:
            info.duration = metadata.get("duration")

    @classmethod
    async def __create_cached_video(cls, info: InfoVideoTikTok) -> Path:
        video = await HttpService.get(info.video_url) if info.video_url else None
        cache_dir = _TikTokCacheDir()
        scheduled = False
        try:
            await wait_for_completion(cls.__prepare_video(info, cache_dir, video))
            await cache_dir.delete_after(minutes=5)
            scheduled = True
            return Path(cache_dir.get_file_path("video.mp4"))
        finally:
            if not scheduled:
                await cache_dir._delete()

    @classmethod
    async def __prepare_video(
        cls, info: InfoVideoTikTok, cache_dir: CacheDir, video: bytes | None
    ) -> None:
        if video is not None:
            await asyncio.to_thread(cache_dir.save_file, "video.mp4", video)
        elif info.images_urls:
            await SlideshowRenderer.make_slideshow_file_from_web(
                info.images_urls, info.music_url, cache_dir.get_file_path("video.mp4")
            )
        else:
            raise TikTokInfoExtractionFailed("")
