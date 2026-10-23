import os
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, replace
from subprocess import SubprocessError
from typing import Any, cast

import yt_dlp
from aiogram.types import FSInputFile, InputFile, URLInputFile

from services.ffmpeg import FfmpegService
from services.video import cover_url, start_timestamp
from utils.async_wrapper import async_wrap
from workers.yt_dlp import download_video, get_info

from ._types import AudioFileInfo, VideoFileInfo
from .options_manager import YtDlpOptionsManager


@dataclass(frozen=True)
class _YtDlpInfo:
    duration: int
    title: str
    height: int | None
    width: int | None
    cover: str | None = None
    start_timestamp: int | None = None


class YtdlpDownloader:
    @classmethod
    @asynccontextmanager
    async def download_audio(cls, url: str) -> AsyncIterator[AudioFileInfo]:
        info = await cls._get_info(url)
        opts, cache_dir = YtDlpOptionsManager.choose_audio_options(url)
        try:
            file = await cls._download_file(url, opts)
            if isinstance(file, URLInputFile):
                output_path = cast(str, opts["outtmpl"])
                await FfmpegService.download_and_prepare_audio(
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
        info = await cls._get_info(url)
        opts, cache_dir = YtDlpOptionsManager.choose_video_options(url)
        try:
            if any(
                processor.get("remove_sponsor_segments")
                for processor in opts.get("postprocessors", [])
            ):
                # Source timestamps no longer refer to the edited timeline.
                info = replace(info, start_timestamp=None)
            file = await cls._download_file(url, opts)
            info = await cls._fill_missing_metadata(info, file)

            yield VideoFileInfo(
                input_file=file,
                duration=info.duration,
                title=info.title,
                height=info.height,
                width=info.width,
                cover=info.cover,
                start_timestamp=info.start_timestamp,
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
            metadata = await FfmpegService.get_video_metadata(str(file.path))
        except SubprocessError:
            return info

        return replace(
            info,
            duration=info.duration or metadata.get("duration", 0),
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
            cover=cls._get_cover(raw_info),
            start_timestamp=start_timestamp(
                raw_info.get("start_time"), raw_info.get("duration")
            ),
        )

    @staticmethod
    def _get_cover(raw_info: dict[str, Any]) -> str | None:
        # Telegram fetches cover URLs itself, without yt-dlp cookies/headers.
        # yt-dlp orders thumbnails from worst to best. A JPEG fallback is
        # useful when the preferred image is WebP or a storyboard.
        thumbnails = raw_info.get("thumbnails")
        preferred = raw_info.get("thumbnail")
        candidates = []
        if isinstance(thumbnails, list):
            if not any(
                isinstance(thumbnail, dict)
                and thumbnail.get("url") == preferred
                and thumbnail.get("http_headers")
                for thumbnail in thumbnails
            ):
                candidates.append(preferred)
            candidates.extend(
                thumbnail.get("url")
                for thumbnail in reversed(thumbnails)
                if isinstance(thumbnail, dict) and not thumbnail.get("http_headers")
            )
        else:
            candidates.append(preferred)
        return next((url for value in candidates if (url := cover_url(value))), None)

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
