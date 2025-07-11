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
    default = {}
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
