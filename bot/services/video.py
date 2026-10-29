"""Optional presentation metadata shared by video download providers."""

from dataclasses import dataclass
from typing import TypedDict
from urllib.parse import urlsplit

from aiogram.types import InputFile


class VideoSendOptions(TypedDict, total=False):
    cover: str | InputFile
    start_timestamp: int


def cover_url(value: object) -> str | None:
    """Accept public JPEG/PNG URLs that Telegram can fetch without headers."""
    if not isinstance(value, str) or any(char.isspace() for char in value):
        return None
    try:
        url = urlsplit(value)
        if (
            url.scheme not in {"http", "https"}
            or not url.hostname
            or url.username is not None
            or url.password is not None
            or not url.path.lower().endswith((".jpg", ".jpeg", ".png"))
        ):
            return None
        # Accessing port also rejects malformed port numbers.
        _ = url.port
    except ValueError:
        return None
    return value


def start_timestamp(value: object, duration: float | None) -> int | None:
    """Convert provider seconds to Telegram seconds, never an upload date."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not 0 <= value <= 2**31 - 1
        or (isinstance(duration, (int, float)) and duration > 0 and value >= duration)
    ):
        return None
    return int(value)


@dataclass(kw_only=True)
class VideoMetadata:
    cover: str | InputFile | None = None
    start_timestamp: int | None = None

    def send_options(self, duration: int | None = None) -> VideoSendOptions:
        options: VideoSendOptions = {}
        if isinstance(self.cover, InputFile):
            options["cover"] = self.cover
        elif url := cover_url(self.cover):
            options["cover"] = url
        if (timestamp := start_timestamp(self.start_timestamp, duration)) is not None:
            options["start_timestamp"] = timestamp
        return options
