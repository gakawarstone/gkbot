from dataclasses import dataclass

from aiogram.types import InputFile

from services.video import VideoMetadata


@dataclass
class InfoVideoTikTok(VideoMetadata):
    video_url: str | None
    video_input_file: InputFile | None
    music_url: str | None
    images_urls: list[str] | None
    height: int | None = None
    width: int | None = None
    duration: int | None = None


@dataclass
class TikTokVideo(VideoMetadata):
    input_file: InputFile
    url: str | None = None
    height: int | None = None
    width: int | None = None
    duration: int | None = None
