from subprocess import SubprocessError

from aiogram.types import BufferedInputFile, FSInputFile

from services.http import HttpService
from services.ffmpeg import FfmpegService
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
        info = await cls.get_video_info(url)

        if not (input_file := info.video_input_file):
            input_file = BufferedInputFile(
                file=await cls.__get_video_file_from_info(info),
                filename="video.mp4",
            )

        return TikTokVideo(
            url=info.video_url,
            input_file=input_file,
            height=info.height,
            width=info.width,
            duration=info.duration,
        )

    @classmethod
    async def get_video_info(cls, url: str) -> InfoVideoTikTok:
        if not (info := await TikTokInfoExtractor.get_video_info(url)):
            raise TikTokInfoExtractionFailed(url)
        await cls.__fill_missing_video_metadata(info)
        return info

    @classmethod
    async def __fill_missing_video_metadata(cls, info: InfoVideoTikTok) -> None:
        if info.height and info.width and info.duration:
            return

        if not isinstance(info.video_input_file, FSInputFile):
            return
        source = str(info.video_input_file.path)

        try:
            metadata = await FfmpegService.get_video_metadata(source)
        except SubprocessError:
            return
        if not info.height:
            info.height = metadata.get("height")
        if not info.width:
            info.width = metadata.get("width")
        if not info.duration:
            info.duration = metadata.get("duration")

    @classmethod
    async def __get_video_file_from_info(cls, info: InfoVideoTikTok) -> bytes:
        if video_url := info.video_url:
            return await HttpService.get(video_url)
        if info.images_urls:
            return await FfmpegService.make_slideshow_from_web(
                info.images_urls, info.music_url
            )
        raise TikTokInfoExtractionFailed("")
