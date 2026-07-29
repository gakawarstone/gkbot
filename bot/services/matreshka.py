import html
import re
from dataclasses import dataclass
from urllib.parse import urlparse

from aiogram.types import FSInputFile
from bs4 import BeautifulSoup, Tag
from services.cache_dir import CacheDir
from services.ffmpeg import FfmpegService
from services.http import HttpService
from services.open_graph import OpenGraphService
from services.ytdlp._types import AudioFileInfo

_HLS_URL_PATTERN = re.compile(r'https:(?:\\u002F){2}[^"]+?master\.m3u8\?[^"]+')


class InvalidMatreshkaVideoUrl(ValueError):
    """Raised when a URL does not identify a Matreshka video."""


class MatreshkaVideoUnavailable(ValueError):
    """Raised when Matreshka does not expose a playable video stream."""


@dataclass(frozen=True, slots=True)
class MatreshkaVideo:
    id: str
    title: str
    duration: int
    image_url: str | None
    hls_url: str


class MatreshkaService:
    @staticmethod
    def get_video_id(url: str) -> str:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip("/").split("/")
        if (
            parsed_url.hostname not in {"matreshka.tv", "www.matreshka.tv"}
            or len(path_parts) != 2
            or path_parts[0] != "video"
            or not path_parts[1]
        ):
            raise InvalidMatreshkaVideoUrl(url)

        return path_parts[1]

    @classmethod
    async def get_video(cls, url: str) -> MatreshkaVideo:
        video_id = cls.get_video_id(url)
        page = await HttpService.get(url)
        return cls.parse_video(page, video_id)

    @staticmethod
    def parse_video(page: bytes | str, video_id: str) -> MatreshkaVideo:
        page_text = page.decode() if isinstance(page, bytes) else page
        hls_urls = _HLS_URL_PATTERN.findall(page_text)
        if not hls_urls:
            raise MatreshkaVideoUnavailable(video_id)

        metadata = OpenGraphService.parse(page_text)
        soup = BeautifulSoup(page_text, "html.parser")
        duration_tag = soup.find("meta", attrs={"property": "video:duration"})

        duration = 0
        if isinstance(duration_tag, Tag):
            raw_duration = duration_tag.get("content")
            if isinstance(raw_duration, str):
                try:
                    duration = int(raw_duration)
                except ValueError:
                    pass

        hls_url = html.unescape(hls_urls[0].replace(r"\u002F", "/"))
        return MatreshkaVideo(
            id=video_id,
            title=metadata.title or "МатрёшкаТВ",
            duration=duration,
            image_url=metadata.image_url,
            hls_url=hls_url,
        )

    @staticmethod
    async def download_audio(video: MatreshkaVideo) -> AudioFileInfo:
        cache_dir = CacheDir()
        await cache_dir.delete_after(minutes=5)
        await FfmpegService.download_and_prepare_audio(video.hls_url, cache_dir.path)

        return AudioFileInfo(
            input_file=FSInputFile(cache_dir.get_file_path("audio.m4a")),
            duration=video.duration,
            title=video.title,
        )
