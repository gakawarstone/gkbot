from dataclasses import dataclass
from pathlib import Path


@dataclass
class AudioFileInfo:
    path: Path
    duration: int
    title: str


@dataclass
class VideoFileInfo:
    file: Path | str
    height: int | None
    width: int | None
    duration: int
    title: str


# Previously DownloadOptions was an Enum; simplify to a plain base class for namespacing.
class DownloadOptions:
    pass
