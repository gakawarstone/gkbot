import os
from pathlib import Path

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
            return ExtractedVideoData(
                video_file=video_file_info.file,
                duration=video_file_info.duration,
                height=video_file_info.height,
                width=video_file_info.width,
            )

    async def get_video_file_url(self, url: str) -> str:
        with self._translate_errors():
            serveo_url = self._get_serveo_url()
            if not serveo_url:
                raise ValueError("Serveo URL is missing")
            async with YtdlpDownloader.download_video(
                url, cleanup_delay_minutes=5
            ) as video_file_info:
                file = video_file_info.file
                if not isinstance(file, Path):
                    raise TypeError("Serveo requires a local video file")
                video_path = "/".join(file.parts[-3:])
                return serveo_url + "/" + video_path

    @classmethod
    def _get_serveo_url(cls) -> str | None:
        url_path = Path(os.path.expanduser(CACHE_DIR_PATH + "/serveo_url"))
        try:
            serveo_url = url_path.read_text().strip()
        except OSError:
            return None
        return serveo_url or None
