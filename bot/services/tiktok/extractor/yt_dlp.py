import os
from pathlib import Path

from aiogram.types import InputFile, FSInputFile
from yt_dlp.utils import DownloadError

from configs.services.cache_dir import CACHE_DIR_PATH
from services.ytdlp import YtdlpDownloader
from services.ytdlp._types import VideoFileInfo
from ..types import InfoVideoTikTok
from .exceptions import SourceInfoExtractFailed
from ._base import BaseExtractor


class YtDlp(BaseExtractor):
    async def get_video_info(self, url: str) -> InfoVideoTikTok:
        try:
            video_file_info = await YtdlpDownloader.download_video(url)
            return InfoVideoTikTok(
                video_url=None,
                video_input_file=video_file_info.input_file,
                music_url="",
                images_urls=[],
                duration=video_file_info.duration,
                height=video_file_info.height,
                width=video_file_info.width,
            )
        except (IndexError, ValueError, DownloadError):
            raise SourceInfoExtractFailed(self)

    async def _get_video_input_file(self, url: str) -> InputFile:
        return (await YtdlpDownloader.download_video(url)).input_file

    async def get_video_file_url(self, url: str) -> str:
        try:
            if not self._get_serveo_url():
                raise ValueError("Serveo URL is missing")
            video_file_info = await YtdlpDownloader.download_video(url)
            return await self._get_video_file_url_from_info(video_file_info)
        except (IndexError, ValueError, OSError, DownloadError):
            raise SourceInfoExtractFailed(self)

    async def _get_video_file_url_from_info(
        self, video_file_info: VideoFileInfo
    ) -> str:
        try:
            fs_input_file = video_file_info.input_file
            if not isinstance(fs_input_file, FSInputFile):
                raise ValueError("Input file is not an FSInputFile instance")

            serveo_url = self._get_serveo_url()
            if serveo_url is None:
                raise ValueError("Serveo URL is missing")

            video_path = "/".join(str(fs_input_file.path).split("/")[-3:])
            return serveo_url + "/" + video_path
        except (IndexError, ValueError, DownloadError):
            raise SourceInfoExtractFailed(self)

    @classmethod
    def _get_serveo_url(cls) -> str | None:
        url_path = Path(os.path.expanduser(CACHE_DIR_PATH + "/serveo_url"))
        try:
            serveo_url = url_path.read_text().strip()
        except OSError:
            return None
        return serveo_url or None
