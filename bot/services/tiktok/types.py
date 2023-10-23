from dataclasses import dataclass
from typing import Optional


@dataclass
class InfoVideoTikTok:
    video_url: Optional[str]
    music_url: Optional[str]
    images_urls: Optional[list[str]]
