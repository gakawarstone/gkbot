from subprocess import SubprocessError

from aiogram.types import FSInputFile

from services.cache_dir import CacheDir
from services.ffmpeg import FfmpegService
from services.http import HttpService

from .exceptions import TikTokInfoExtractionFailed, TikTokVideoUrlExtractionFailed
from .extractor import TikTokInfoExtractor
from .types import InfoVideoTikTok, TikTokVideo


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
        video = await cls.__resolve_video_bytes(info)
        cache_dir = CacheDir()
        cache_dir.save_file("video.mp4", video)
        await cache_dir.delete_after(minutes=5)
        return FSInputFile(cache_dir.get_file_path("video.mp4"))

    @classmethod
    async def __resolve_video_bytes(cls, info: InfoVideoTikTok) -> bytes:
        if video_url := info.video_url:
            return await HttpService.get(video_url)
        if info.images_urls:
            return await FfmpegService.make_slideshow_from_web(
                info.images_urls, info.music_url
            )
        raise TikTokInfoExtractionFailed("")
