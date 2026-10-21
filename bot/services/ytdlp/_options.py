from typing import Any, ClassVar

from ._types import DownloadOptions


class AudioDownloadOptions(DownloadOptions):
    youtube: ClassVar[dict[str, Any]] = {
        "format": "ba[ext=m4a]/ba/b",
        "postprocessors": [
            {"key": "SponsorBlock", "categories": ["sponsor"]},
            {"key": "ModifyChapters", "remove_sponsor_segments": ["sponsor"]},
        ],
    }

    vk: ClassVar[dict[str, Any]] = {
        "format": "ba",
        "concurrent_fragment_downloads": 100,
        "force_ipv4": True,
    }


class VideoDownloadOptions(DownloadOptions):
    default: ClassVar[dict[str, Any]] = {}
    youtube_shorts: ClassVar[dict[str, Any]] = {
        "format": "bv*+ba/b",
        "external_downloader": "aria2c",
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
    }

    youtube: ClassVar[dict[str, Any]] = {
        # Combined YouTube formats commonly omit filesize, so keep the size
        # guard only on the adaptive-stream path.
        "format": ("bv[ext=mp4][filesize<1G][vcodec^=avc1]+ba[ext=m4a]/b[ext=mp4]"),
        "external_downloader": "aria2c",
        "external_downloader_args": [
            "-x",
            "16",
            "-k",
            "1M",
        ],
        "postprocessors": [
            {"key": "SponsorBlock", "categories": ["sponsor"]},
            {"key": "ModifyChapters", "remove_sponsor_segments": ["sponsor"]},
        ],
    }

    tiktok: ClassVar[dict[str, Any]] = {
        # TikTok exposes very large HD variants for some posts. Prefer a compact,
        # Telegram-compatible muxed stream so it can be uploaded as-is instead of
        # being transcoded into an even larger file.
        "format": (
            "b[ext=mp4][vcodec^=h264][acodec!=none][filesize<20M]"
            "/b[ext=mp4][vcodec^=h264][acodec!=none][filesize_approx<20M]"
            "/b[ext=mp4][vcodec^=h264][acodec!=none][width<=720]"
            "/b[ext=mp4][vcodec^=h264][acodec!=none]"
        ),
    }

    vk: ClassVar[dict[str, Any]] = {
        "format": "bv[ext=mp4]+ba[ext=m4a]/b[ext=mp4]",
        "concurrent_fragment_downloads": 100,
        "force_ipv4": True,
    }
