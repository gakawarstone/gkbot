from typing import Any

from services.cache_dir import CacheDir

from ._options import AudioDownloadOptions, VideoDownloadOptions
from .source import DownloadSource


class YtDlpOptionsManager:
    @classmethod
    def choose_audio_options(
        cls, source: DownloadSource
    ) -> tuple[dict[str, Any], CacheDir]:
        opts: dict[str, Any] = {}
        if source in (DownloadSource.VK, DownloadSource.VK_CLIP):
            opts.update(AudioDownloadOptions.vk)
        else:
            opts.update(AudioDownloadOptions.youtube)

        cache_dir = CacheDir()
        opts["outtmpl"] = cache_dir.get_file_path("audio.m4a")
        return opts, cache_dir

    @classmethod
    def choose_video_options(
        cls, source: DownloadSource
    ) -> tuple[dict[str, Any], CacheDir]:
        presets: dict[DownloadSource, dict[str, Any]] = {
            DownloadSource.YOUTUBE: VideoDownloadOptions.youtube,
            DownloadSource.YOUTUBE_SHORTS: VideoDownloadOptions.youtube_shorts,
            DownloadSource.TIKTOK: VideoDownloadOptions.tiktok,
            DownloadSource.VK_CLIP: VideoDownloadOptions.tiktok,
            DownloadSource.VK: VideoDownloadOptions.vk,
        }
        opts: dict[str, Any] = dict(presets.get(source, VideoDownloadOptions.default))

        cache_dir = CacheDir()
        opts["outtmpl"] = cache_dir.get_file_path("video.mp4")
        return opts, cache_dir
