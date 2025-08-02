from dataclasses import dataclass

from aiogram.types import InputFile


@dataclass
class AudioFileInfo:
    input_file: InputFile
    duration: int
    title: str


@dataclass
class VideoFileInfo:
    input_file: InputFile
    height: int
    width: int
    duration: int
    title: str


# Previously DownloadOptions was an Enum; simplify to a plain base class for namespacing.
class DownloadOptions:
    pass

