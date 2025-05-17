import re

from services.cache_dir import CacheDir
from ._options import VideoDownloadOptions, AudioDownloadOptions


class YtDlpOptionsManager:
    @classmethod
    def choose_audio_options(cls, url: str) -> dict:
        opts = AudioDownloadOptions.youtube
        if url.startswith("https://vk.com"):
            opts = AudioDownloadOptions.vk

        opts = opts.value.copy()
        opts["outtmpl"] = CacheDir().path + "/" + "audio.m4a"
        return opts

    @classmethod
    def choose_video_options(cls, url: str) -> dict:
        opts = VideoDownloadOptions.default

        _yt_pattern = (
            r"http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?"
            r"v=|\.be\/)([\w\-\_]*)(&(amp;)?[\w\?=]*)?"
        )
        if re.match(_yt_pattern, url):
            opts = VideoDownloadOptions.youtube
        if re.match(r"^https://(www\.)?youtube\.com/shorts", url):
            opts = VideoDownloadOptions.youtube_shorts
        if re.match(r"https://(www|vm|vr|vt).tiktok.com/", url):
            opts = VideoDownloadOptions.tiktok
        if url.startswith("https://vk.com/clip-"):
            opts = VideoDownloadOptions.tiktok

        opts = opts.value.copy()
        opts["outtmpl"] = CacheDir().path + "/" + "video.mp4"
        return opts
