import os
from typing import Any
import re

import yt_dlp
from aiogram.types import FSInputFile, InputFile, URLInputFile

from services.ffmpeg import FfmpegService
from utils.async_wrapper import async_wrap
from workers.yt_dlp import get_info, download_video
from ._types import AudioFileInfo, VideoFileInfo
from .options_manager import YtDlpOptionsManager


class YtdlpDownloader:
    @classmethod
    async def download_audio(cls, url: str) -> AudioFileInfo:
        info = await cls._get_info(url)
        opts = await YtDlpOptionsManager.choose_audio_options(url)
        file = await cls._download_file(url, opts)

        return AudioFileInfo(
            input_file=file,
            duration=info["duration"],
            title=info["title"],
        )

    @classmethod
    async def download_video(cls, url: str) -> VideoFileInfo:
        info = await cls._get_info(url)
        opts = await YtDlpOptionsManager.choose_video_options(url)
        file = await cls._download_file(url, opts)

        width = info.get("width", 0)

        return VideoFileInfo(
            input_file=file,
            duration=info["duration"],
            title=info["title"],
            height=info["height"],
            width=width,
        )

    @classmethod
    async def _get_info(cls, url: str) -> dict[str, Any]:
        if re.match(r"^https://(?:www\.)?youtu", url):
            return await get_info(url)

        with yt_dlp.YoutubeDL() as ydl:
            info = await async_wrap(ydl.extract_info)(url, download=False)

        if not info:
            raise Exception

        return info

    @classmethod
    async def _download_file(cls, url: str, opts: dict) -> InputFile:
        if re.match(r"^https://(?:www\.)?youtu", url):
            url = await download_video(url, opts)
            return URLInputFile(url)

        with yt_dlp.YoutubeDL(opts) as ydl:
            await async_wrap(ydl.download)(url)

        output_path = opts["outtmpl"]["default"]
        if not os.path.exists(output_path):
            postprocessor = opts["postprocessors"][0]
            if "preferedformat" in postprocessor:
                output_path += "." + postprocessor["preferedformat"]
            if "preferredcodec" in postprocessor:
                output_path += "." + postprocessor["preferredcodec"]

        if "instagram.com/reel" in url:
            base, _ = os.path.splitext(output_path)
            converted_path = f"{base}_converted.mp4"
            await FfmpegService.convert_video(output_path, converted_path)
            output_path = converted_path

        return FSInputFile(output_path)
