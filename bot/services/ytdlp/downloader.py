import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from subprocess import SubprocessError
from typing import Any, cast

import yt_dlp
from aiogram.types import FSInputFile, InputFile, URLInputFile

from services.audio import AudioService
from services.video_conversion import VideoConversionService
from services.video_metadata import VideoMetadataService
from utils.async_wrapper import async_wrap
from workers.yt_dlp import download_video, get_info

from ._types import AudioFileInfo, VideoFileInfo
from .options_manager import YtDlpOptionsManager
from .source import DownloadSource, classify_source


@dataclass(frozen=True)
class _YtDlpInfo:
    duration: int
    title: str
    height: int | None
    width: int | None


class YtdlpDownloader:
    @classmethod
    @asynccontextmanager
    async def download_audio(cls, url: str) -> AsyncIterator[AudioFileInfo]:
        source = classify_source(url)
        info = await cls._get_info(url, source)
        opts, cache_dir = YtDlpOptionsManager.choose_audio_options(source)
        try:
            file = await cls._download_file(url, opts, source)
            if isinstance(file, URLInputFile):
                output_path = cast(str, opts["outtmpl"])
                await AudioService.download_and_prepare_audio(
                    file.url, os.path.dirname(output_path)
                )
                file = FSInputFile(output_path)

            yield AudioFileInfo(
                input_file=file,
                duration=info.duration,
                title=info.title,
            )
        finally:
            cache_dir.delete()

    @classmethod
    @asynccontextmanager
    async def download_video(
        cls, url: str, cleanup_delay_minutes: int | None = None
    ) -> AsyncIterator[VideoFileInfo]:
        source = classify_source(url)
        info = await cls._get_info(url, source)
        opts, cache_dir = YtDlpOptionsManager.choose_video_options(source)
        try:
            file = await cls._download_file(url, opts, source)
            info = await cls._fill_missing_metadata(info, file)

            yield VideoFileInfo(
                input_file=file,
                duration=info.duration,
                title=info.title,
                height=info.height,
                width=info.width,
            )
        finally:
            if cleanup_delay_minutes is None:
                cache_dir.delete()
            else:
                await cache_dir.delete_after(minutes=cleanup_delay_minutes)

    @classmethod
    async def _fill_missing_metadata(
        cls, info: _YtDlpInfo, file: InputFile
    ) -> _YtDlpInfo:
        if not isinstance(file, FSInputFile) or (
            info.duration and info.height and info.width
        ):
            return info

        try:
            metadata = await VideoMetadataService.get_video_metadata(str(file.path))
        except SubprocessError:
            return info

        return _YtDlpInfo(
            duration=info.duration or metadata.get("duration", 0),
            title=info.title,
            height=info.height or metadata.get("height"),
            width=info.width or metadata.get("width"),
        )

    @classmethod
    async def _get_info(cls, url: str, source: DownloadSource) -> _YtDlpInfo:
        if source.uses_worker:
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
    async def _download_file(
        cls, url: str, opts: dict[str, Any], source: DownloadSource
    ) -> InputFile:
        if source.uses_worker:
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

        if source.needs_video_conversion:
            base, _ = os.path.splitext(output_path)
            converted_path = f"{base}_converted.mp4"
            await VideoConversionService.convert_video(output_path, converted_path)
            output_path = converted_path

        return FSInputFile(output_path)
