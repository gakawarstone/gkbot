from io import BytesIO

from aiogram.types import BufferedInputFile

from tiktok_downloader import snaptik
from tiktok_downloader.Except import InvalidUrl


class TikTokInvalidUrl(InvalidUrl):
    def __init__(self, url: str) -> None:
        self.url = url

    def __str__(self) -> str:
        return f'Invalid url {self.url}'


class TikTokDownloader:
    @classmethod
    def __download_video(cls, url: str) -> BytesIO:
        return snaptik(url).get_media()[0].download()

    @classmethod
    def download_as_input_file(cls, url: str) -> BufferedInputFile:
        try:
            return BufferedInputFile(
                cls.__download_video(url).getvalue(), 'video.mp4')
        except InvalidUrl:
            raise TikTokInvalidUrl(url)
