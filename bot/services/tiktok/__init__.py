from aiogram.types import BufferedInputFile

from services.http import HttpService
from services.ffmpeg import FfmpegService
from .exceptions import TikTokInfoExtractionFailed, TikTokVideoUrlExtractionFailed
from .extractor import TikTokInfoExtractor


class TikTokService:
    @classmethod
    async def get_video_url(cls, url: str) -> str:
        if video_url := await TikTokInfoExtractor.get_video_url(url):
            return video_url
        raise TikTokVideoUrlExtractionFailed(url)

    @classmethod
    async def get_video_as_input_file(cls, url: str) -> BufferedInputFile:
        if not (info := await TikTokInfoExtractor.get_video_info(url)):
            raise TikTokInfoExtractionFailed(url)
        if not info.video_input_file:
            return BufferedInputFile(
                file=await cls.__get_video_file(url), filename="video.mp4"
            )
        return info.video_input_file

    @classmethod
    async def __get_video_file(cls, url: str) -> bytes:
        if not (info := await TikTokInfoExtractor.get_video_info(url)):
            raise TikTokInfoExtractionFailed(url)
        if video_url := info.video_url:
            return await HttpService.get(video_url)
        if info.images_urls:
            return await FfmpegService.make_slideshow_from_web(
                info.images_urls, info.music_url
            )
        raise TikTokInfoExtractionFailed(url)
