from dataclasses import dataclass
from typing import Optional

from aiogram.types import InputFile


@dataclass
class InfoVideoTikTok:
    video_url: Optional[str]
    video_input_file: Optional[InputFile]
    music_url: Optional[str]
    images_urls: Optional[list[str]]
    height: Optional[int] = None
    width: Optional[int] = None
    duration: Optional[int] = None


@dataclass
class TikTokVideo:
    input_file: InputFile
    url: str | None = None
    height: int | None = None
    width: int | None = None
    duration: int | None = None
