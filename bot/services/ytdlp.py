import os
import re
from dataclasses import dataclass
from enum import Enum

import yt_dlp
from aiogram.types import BufferedInputFile, FSInputFile

from workers.yt_dlp import YtdlpWorker
from utils.async_wrapper import async_wrap
from services.cache_dir import CacheDir


@dataclass
class AudioFileInfo:
    input_file: BufferedInputFile | FSInputFile
    duration: int
    title: str


class DownloadOptions(Enum):
    pass


# FIXME: move to separate file
class AudioDownloadOptions(DownloadOptions):
    youtube = {
        "format": "ba[ext=m4a]",
        "postprocessors": [
            {"key": "SponsorBlock", "categories": ["sponsor"]},
            {"key": "ModifyChapters", "remove_sponsor_segments": ["sponsor"]},
        ],
    }

    vk = {
        "format": "ba",
        "concurrent_fragment_downloads": 100,
        "force_ipv4": True,
    }


class VideoDownloadOptions(DownloadOptions):
    youtube_shorts = {
        "format": "bv+ba",
        "external_downloader": "aria2c",
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
    }

    youtube = {
        "format": "136+140",
        "postprocessors": [
            {"key": "SponsorBlock", "categories": ["sponsor"]},
            {"key": "ModifyChapters", "remove_sponsor_segments": ["sponsor"]},
        ],
    }

    tiktok = {
        "format": "mp4",
    }


class YtdlpDownloader:
    @classmethod
    async def download_audio(cls, url: str) -> AudioFileInfo:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)

        return AudioFileInfo(
            input_file=await cls.__download_audio_file(url),
            duration=info["duration"],
            title=info["title"],
        )

    # FIXME: api must be same with download audio
    @classmethod
    async def download_video(cls, url: str) -> FSInputFile:
        if url.startswith("https://youtube.com/shorts"):
            path = await YtdlpWorker().download(url)  # FIXME: classmethod
            return FSInputFile(path, "video.mp4")
        opts = cls.__choose_video_opts(url)
        return await cls.__download_file(url, opts, "video.mp4")

    @classmethod
    async def __download_audio_file(cls, url: str) -> FSInputFile:
        opts = cls.__choose_audio_opts(url)
        file = await cls.__download_file(url, opts, "audio.m4a")
        return file

    @classmethod
    @async_wrap
    def __download_file(
        cls, url: str, opts: DownloadOptions, file_name: str
    ) -> FSInputFile:
        output_path = cls.__prepare_path() + "/" + file_name
        opts = opts.value.copy()
        opts["outtmpl"] = output_path

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download(url)

        if not os.path.exists(output_path):
            postprocessor = opts["postprocessors"][0]
            if "preferedformat" in postprocessor:
                output_path += "." + postprocessor["preferedformat"]
            if "preferredcodec" in postprocessor:
                output_path += "." + postprocessor["preferredcodec"]

        return FSInputFile(output_path, file_name)

    @staticmethod
    def __choose_audio_opts(url: str) -> DownloadOptions:
        # FIXME: refactor it use filters
        if url.startswith("https://vk.com"):
            return AudioDownloadOptions.vk
        return AudioDownloadOptions.youtube

    @staticmethod
    def __choose_video_opts(url: str) -> DownloadOptions:
        if re.match(r"^https://(www\.)?youtube\.com/shorts", url):
            return VideoDownloadOptions.youtube_shorts
        if re.match(r"https://(www|vm|vr|vt).tiktok.com/", url):
            return VideoDownloadOptions.tiktok
        return VideoDownloadOptions.youtube

    @staticmethod
    def __prepare_path() -> str:
        cache_dir = CacheDir()
        return cache_dir.path
