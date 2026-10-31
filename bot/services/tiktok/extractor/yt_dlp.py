import os
from pathlib import Path

from aiogram.types import FSInputFile, InputFile
from yt_dlp.utils import DownloadError

from configs.services.cache_dir import CACHE_DIR_PATH
from services.ytdlp import YtdlpDownloader

from ._base import BaseExtractor, ExtractedVideoData


class YtDlp(BaseExtractor):
    _expected_errors = (*BaseExtractor._expected_errors, OSError, DownloadError)

    async def _extract_video_data(self, url: str) -> ExtractedVideoData:
        async with YtdlpDownloader.download_video(
            url, cleanup_delay_minutes=5
        ) as video_file_info:
            return {
                "video_input_file": video_file_info.input_file,
                "duration": video_file_info.duration,
                "height": video_file_info.height,
                "width": video_file_info.width,
            }

    async def _get_video_input_file(self, url: str) -> InputFile:
        async with YtdlpDownloader.download_video(
            url, cleanup_delay_minutes=5
        ) as video_file_info:
            return video_file_info.input_file

    async def get_video_file_url(self, url: str) -> str:
        with self._translate_errors():
            serveo_url = self._get_serveo_url()
            if not serveo_url:
                raise ValueError("Serveo URL is missing")
            async with YtdlpDownloader.download_video(
                url, cleanup_delay_minutes=5
            ) as video_file_info:
                input_file = video_file_info.input_file
                if not isinstance(input_file, FSInputFile):
                    raise TypeError("Input file is not an FSInputFile instance")
                video_path = "/".join(str(input_file.path).split("/")[-3:])
                return serveo_url + "/" + video_path

    @classmethod
    def _get_serveo_url(cls) -> str | None:
        url_path = Path(os.path.expanduser(CACHE_DIR_PATH + "/serveo_url"))
        try:
            serveo_url = url_path.read_text().strip()
        except OSError:
            return None
        return serveo_url or None
