import os
import re
from subprocess import SubprocessError
from typing import Any, cast
from dataclasses import dataclass

import yt_dlp
from aiogram.types import FSInputFile, InputFile, URLInputFile

from services.ffmpeg import FfmpegService
from utils.async_wrapper import async_wrap
from workers.yt_dlp import get_info, download_video
from ._types import AudioFileInfo, VideoFileInfo
from .options_manager import YtDlpOptionsManager


@dataclass(frozen=True)
class _YtDlpInfo:
    duration: int
    title: str
    height: int | None
    width: int | None


class YtdlpDownloader:
    @classmethod
    async def download_audio(cls, url: str) -> AudioFileInfo:
        info = await cls._get_info(url)
        opts = await YtDlpOptionsManager.choose_audio_options(url)
        file = await cls._download_file(url, opts)

        return AudioFileInfo(
            input_file=file,
            duration=info.duration,
            title=info.title,
        )

    @classmethod
    async def download_video(cls, url: str) -> VideoFileInfo:
        info = await cls._get_info(url)
        opts = await YtDlpOptionsManager.choose_video_options(url)
        file = await cls._download_file(url, opts)
        info = await cls._fill_missing_metadata(info, file)

        return VideoFileInfo(
            input_file=file,
            duration=info.duration,
            title=info.title,
            height=info.height,
            width=info.width,
        )

    @classmethod
    async def _fill_missing_metadata(
        cls, info: _YtDlpInfo, file: InputFile
    ) -> _YtDlpInfo:
        if not isinstance(file, FSInputFile) or (
            info.duration and info.height and info.width
        ):
            return info

        try:
            metadata = await FfmpegService.get_video_metadata(str(file.path))
        except SubprocessError:
            return info

        return _YtDlpInfo(
            duration=info.duration or metadata.get("duration", 0),
            title=info.title,
            height=info.height or metadata.get("height"),
            width=info.width or metadata.get("width"),
        )

    @classmethod
    async def _get_info(cls, url: str) -> _YtDlpInfo:
        if re.match(r"^https://(?:www\.)?youtu", url):
            raw_info = await get_info(url)
        else:
            with yt_dlp.YoutubeDL() as ydl:
                raw_info = await async_wrap(ydl.extract_info)(url, download=False)

        if not isinstance(raw_info, dict):
            raise ValueError("yt-dlp returned invalid metadata")

        return _YtDlpInfo(
            duration=raw_info.get("duration") or 0,
            title=raw_info["title"],
            height=raw_info.get("height") or 0,
            width=raw_info.get("width") or 0,
        )

    @classmethod
    async def _download_file(cls, url: str, opts: dict[str, Any]) -> InputFile:
        if re.match(r"^https://(?:www\.)?youtu", url):
            url = await download_video(url, opts)
            return URLInputFile(url)

        with yt_dlp.YoutubeDL(cast(Any, opts)) as ydl:
            await async_wrap(ydl.download)(url)

        outtmpl = opts["outtmpl"]
        output_path = outtmpl["default"] if isinstance(outtmpl, dict) else outtmpl
        if not os.path.exists(output_path):
            postprocessors = opts.get("postprocessors", [])
            if postprocessors:
                postprocessor = postprocessors[0]
                if "preferedformat" in postprocessor:
                    output_path += "." + postprocessor["preferedformat"]
                if "preferredcodec" in postprocessor:
                    output_path += "." + postprocessor["preferredcodec"]

        if "instagram.com/reel" in url or "tiktok.com" in url:
            base, _ = os.path.splitext(output_path)
            converted_path = f"{base}_converted.mp4"
            await FfmpegService.convert_video(output_path, converted_path)
            output_path = converted_path

        return FSInputFile(output_path)
