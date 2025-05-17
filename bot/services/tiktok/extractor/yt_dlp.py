import os

from aiogram.types import InputFile
from yt_dlp import DownloadError

from configs.services.cache_dir import CACHE_DIR_PATH
from services.ytdlp import YtdlpDownloader
from ..types import InfoVideoTikTok
from .exceptions import SourceInfoExtractFailed
from ._base import BaseExtractor


class YtDlp(BaseExtractor):
    async def get_video_info(self, url: str) -> InfoVideoTikTok:
        try:
            video_url = await self.get_video_file_url(url)
            video_input_file = await self._get_video_input_file(url)
            return InfoVideoTikTok(
                video_url=video_url,
                video_input_file=video_input_file,
                music_url="",
                images_urls=[],
            )
        except (IndexError, ValueError, DownloadError):
            raise SourceInfoExtractFailed(self)

    async def _get_video_input_file(self, url: str) -> InputFile:
        return (await YtdlpDownloader.download_video(url)).input_file

    async def get_video_file_url(self, url: str) -> str:
        try:
            fs_input_file = await self._get_video_input_file(url)
            video_path = "/".join(fs_input_file.path.split("/")[-3:])
            url_path = os.path.expanduser(CACHE_DIR_PATH + "/serveo_url")
            serveo_url = open(url_path).read()
            return serveo_url + "/" + video_path
        except (IndexError, ValueError, DownloadError):
            raise SourceInfoExtractFailed(self)
