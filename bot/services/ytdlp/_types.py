from dataclasses import dataclass

from aiogram.types import InputFile

from services.video import VideoMetadata


@dataclass
class AudioFileInfo:
    input_file: InputFile
    duration: int
    title: str


@dataclass
class VideoFileInfo(VideoMetadata):
    input_file: InputFile
    height: int | None
    width: int | None
    duration: int
    title: str


# Previously DownloadOptions was an Enum; simplify to a plain base class for namespacing.
class DownloadOptions:
    pass
