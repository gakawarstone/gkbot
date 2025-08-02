import re
from typing import Any

from services.cache_dir import CacheDir
from ._options import VideoDownloadOptions, AudioDownloadOptions


class YtDlpOptionsManager:
    @classmethod
    def choose_audio_options(cls, url: str) -> dict[str, Any]:
        # Use a fresh dict to avoid type invariance issues and accidental mutation of class-level dicts
        opts: dict[str, Any] = {}
        if url.startswith("https://vk.com"):
            opts.update(AudioDownloadOptions.vk)
        else:
            opts.update(AudioDownloadOptions.youtube)

        opts["outtmpl"] = CacheDir().path + "/" + "audio.m4a"
        return opts

    @classmethod
    def choose_video_options(cls, url: str) -> dict[str, Any]:
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

        opts["outtmpl"] = CacheDir().path + "/" + "video.mp4"
        return opts
