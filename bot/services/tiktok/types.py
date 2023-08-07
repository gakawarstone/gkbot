from dataclasses import dataclass


@dataclass
class InfoVideoTikTok:
    video_url: str
    music_url: str
    images_urls: list[str]
