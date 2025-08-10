from ._types import DownloadOptions


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
    default: dict = {}
    youtube_shorts = {
        "format": "bv+ba",
        "external_downloader": "aria2c",
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
    }

    youtube = {
        "format": "bv[ext=mp4][height=720]+ba[ext=m4a]",
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

    tiktok = {
        "format": "mp4",
    }
