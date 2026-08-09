import re
from typing import Any

from services.cache_dir import CacheDir

from ._options import AudioDownloadOptions, VideoDownloadOptions


class YtDlpOptionsManager:
    @classmethod
    def choose_audio_options(cls, url: str) -> tuple[dict[str, Any], CacheDir]:
        opts: dict[str, Any] = {}
        if url.startswith(("https://vk.com", "https://vkvideo.ru")):
            opts.update(AudioDownloadOptions.vk)
        else:
            opts.update(AudioDownloadOptions.youtube)

        cache_dir = CacheDir()
        opts["outtmpl"] = cache_dir.get_file_path("audio.m4a")
        return opts, cache_dir

    @classmethod
    def choose_video_options(cls, url: str) -> tuple[dict[str, Any], CacheDir]:
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
        if url.startswith(
            ("https://vk.com", "https://vkvideo.ru")
        ) and not url.startswith("https://vk.com/clip-"):
            opts.update(VideoDownloadOptions.vk)

        cache_dir = CacheDir()
        opts["outtmpl"] = cache_dir.get_file_path("video.mp4")
        return opts, cache_dir
