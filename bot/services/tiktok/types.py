from dataclasses import dataclass
from pathlib import Path


@dataclass
class InfoVideoTikTok:
    video_url: str | None
    video_file: Path | str | None
    music_url: str | None
    images_urls: list[str] | None
    height: int | None = None
    width: int | None = None
    duration: int | None = None


@dataclass
class TikTokVideo:
    file: Path | str
    url: str | None = None
    height: int | None = None
    width: int | None = None
    duration: int | None = None
