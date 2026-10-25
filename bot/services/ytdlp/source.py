from enum import Enum, auto
from urllib.parse import urlsplit


class DownloadSource(Enum):
    UNKNOWN = auto()
    YOUTUBE = auto()
    YOUTUBE_SHORTS = auto()
    TIKTOK = auto()
    INSTAGRAM = auto()
    INSTAGRAM_REEL = auto()
    VK = auto()
    VK_CLIP = auto()

    @property
    def uses_worker(self) -> bool:
        return self in (DownloadSource.YOUTUBE, DownloadSource.YOUTUBE_SHORTS)

    @property
    def needs_video_conversion(self) -> bool:
        return self in (DownloadSource.TIKTOK, DownloadSource.INSTAGRAM_REEL)


def classify_source(url: str) -> DownloadSource:
    """Classify the original URL before any download URL is substituted."""
    try:
        parsed = urlsplit(url)
    except ValueError:
        return DownloadSource.UNKNOWN

    if parsed.scheme not in ("http", "https"):
        return DownloadSource.UNKNOWN

    host = parsed.hostname or ""
    path = parsed.path
    if host in ("youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"):
        if path.startswith("/shorts/"):
            return DownloadSource.YOUTUBE_SHORTS
        return DownloadSource.YOUTUBE
    if host in ("youtu.be", "www.youtu.be"):
        return DownloadSource.YOUTUBE
    if host in (
        "tiktok.com",
        "www.tiktok.com",
        "m.tiktok.com",
        "vm.tiktok.com",
        "vr.tiktok.com",
        "vt.tiktok.com",
    ):
        return DownloadSource.TIKTOK
    if host in ("instagram.com", "www.instagram.com", "m.instagram.com"):
        if path.startswith(("/reel/", "/reels/")):
            return DownloadSource.INSTAGRAM_REEL
        return DownloadSource.INSTAGRAM
    if host in (
        "vk.com",
        "www.vk.com",
        "m.vk.com",
        "vkvideo.ru",
        "www.vkvideo.ru",
        "m.vkvideo.ru",
    ):
        if path.startswith("/clip"):
            clip_id = path.removeprefix("/clip").rstrip("/")
            owner, separator, video = clip_id.partition("_")
            if separator and owner.removeprefix("-").isdigit() and video.isdigit():
                return DownloadSource.VK_CLIP
        return DownloadSource.VK
    return DownloadSource.UNKNOWN
