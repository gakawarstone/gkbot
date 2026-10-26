import asyncio
import os
from collections import Counter
from collections.abc import AsyncGenerator
from contextlib import aclosing
from subprocess import SubprocessError
from typing import ClassVar

from aiogram import Bot
from aiogram.types import FSInputFile

from configs.services.tiktok import MAX_VIDEO_SIZE_BYTES, MAX_VIDEO_WIDTH
from services.cache_dir import CacheDir
from services.ffmpeg import FfmpegService
from services.http import HttpService

from .exceptions import TikTokInfoExtractionFailed, TikTokVideoUrlExtractionFailed
from .extractor import TikTokInfoExtractor
from .types import InfoVideoTikTok, TikTokVideo


class _TikTokCacheDir(CacheDir):
    # Scheduled callbacks are pickled. Keep live upload state at class level so
    # an unpickled callback can still see uploads in this process.
    _active_readers: ClassVar[Counter[str]] = Counter()

    async def _delete(self) -> None:
        if self._active_readers[self.path]:
            await self.delete_after(minutes=5)
            return
        await asyncio.to_thread(self.delete)


class _TikTokInputFile(FSInputFile):
    def __init__(self, cache_dir: _TikTokCacheDir) -> None:
        super().__init__(cache_dir.get_file_path("video.mp4"))
        self._cache_dir = cache_dir

    async def read(self, bot: Bot) -> AsyncGenerator[bytes]:
        readers = self._cache_dir._active_readers
        path = self._cache_dir.path
        readers[path] += 1
        try:
            async with aclosing(super().read(bot)) as chunks:
                async for chunk in chunks:
                    yield chunk
        finally:
            readers[path] -= 1
            if not readers[path]:
                del readers[path]


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

        if info.video_input_file is None:
            info.video_input_file = await cls.__create_cached_input_file(info)

        await cls.__fill_missing_video_metadata(info)

        return TikTokVideo(
            url=info.video_url,
            input_file=info.video_input_file,
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
            info.height = FfmpegService.SLIDESHOW_HEIGHT
            info.width = FfmpegService.SLIDESHOW_WIDTH

        try:
            if isinstance(info.video_input_file, FSInputFile):
                metadata = await FfmpegService.get_video_metadata(
                    str(info.video_input_file.path)
                )
            else:
                return
        except SubprocessError:
            return

        if not info.height:
            info.height = metadata.get("height")
        if not info.width:
            info.width = metadata.get("width")
        if not info.duration:
            info.duration = metadata.get("duration")

    @classmethod
    async def __create_cached_input_file(cls, info: InfoVideoTikTok) -> FSInputFile:
        video = await HttpService.get(info.video_url) if info.video_url else None
        cache_dir = _TikTokCacheDir()
        prepared = asyncio.create_task(cls.__prepare_video(info, cache_dir, video))
        scheduled = False
        try:
            await cls.__wait_for_preparation(prepared)
            await cache_dir.delete_after(minutes=5)
            scheduled = True
            return _TikTokInputFile(cache_dir)
        finally:
            if not scheduled:
                await cache_dir._delete()

    @staticmethod
    async def __wait_for_preparation(prepared: asyncio.Task[None]) -> None:
        """Finish file writes and ffmpeg before allowing cancellation to clean up."""
        cancellation: asyncio.CancelledError | None = None
        while not prepared.done():
            try:
                await asyncio.shield(prepared)
            except asyncio.CancelledError as error:
                if cancellation is None:
                    cancellation = error
        prepared.result()
        if cancellation is not None:
            raise cancellation

    @classmethod
    async def __prepare_video(
        cls, info: InfoVideoTikTok, cache_dir: CacheDir, video: bytes | None
    ) -> None:
        if video is not None:
            await asyncio.to_thread(cache_dir.save_file, "video.mp4", video)
        elif info.images_urls:
            await FfmpegService.make_slideshow_file_from_web(
                info.images_urls, info.music_url, cache_dir.get_file_path("video.mp4")
            )
        else:
            raise TikTokInfoExtractionFailed("")

        video_path = cache_dir.get_file_path("video.mp4")
        compressed_path = await FfmpegService.compress_video_if_needed(
            video_path, max_size_bytes=MAX_VIDEO_SIZE_BYTES, max_width=MAX_VIDEO_WIDTH
        )
        if compressed_path != video_path:
            await asyncio.to_thread(os.replace, compressed_path, video_path)
