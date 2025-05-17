from dataclasses import dataclass
from enum import Enum

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


class DownloadOptions(Enum):
    pass
