import re
from typing import Any

from services.cache_dir import CacheDir
from ._options import VideoDownloadOptions, AudioDownloadOptions


class YtDlpOptionsManager:
    @classmethod
    async def choose_audio_options(cls, url: str) -> dict[str, Any]:
        opts: dict[str, Any] = {}
        if url.startswith("https://vk.com"):
            opts.update(AudioDownloadOptions.vk)
        else:
            opts.update(AudioDownloadOptions.youtube)

        opts["outtmpl"] = await cls._create_path("audio.m4a")
        return opts

    @classmethod
    async def choose_video_options(cls, url: str) -> dict[str, Any]:
        opts: dict[str, Any] = {}

        _yt_pattern = (
            r"http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?"
            r"v=|\.be\/)([\w\-\_]*)(&(amp;)?[\w\?=]*)?"
        )
        if re.match(_yt_pattern, url):
            opts.update(VideoDownloadOptions.youtube)
        if re.match(r"^https://(www\.)?youtube\.com/shorts", url):
            opts.update(VideoDownloadOptions.youtube_shorts)
        if re.match(r"https://(www|vm|vr|vt).tiktok.com/", url):
            opts.update(VideoDownloadOptions.tiktok)
        if url.startswith("https://vk.com/clip-"):
            opts.update(VideoDownloadOptions.tiktok)

        opts["outtmpl"] = await cls._create_path("video.mp4")
        return opts

    @staticmethod
    async def _create_path(file_name: str) -> str:
        cache_dir = CacheDir()
        await cache_dir.delete_after(minutes=5)
        return cache_dir.path + "/" + file_name
