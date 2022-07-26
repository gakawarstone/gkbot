from tiktok_downloader import snaptik
from tiktok_downloader.utils import info_videotiktok
from tiktok_downloader.Except import InvalidUrl


class TikTokInvalidUrl(InvalidUrl):
    def __init__(self, url: str) -> None:
        self.url = url

    def __str__(self) -> str:
        return f'Invalid url {self.url}'


class TikTokDownloader:
    @classmethod
    def __get_video(cls, url: str) -> info_videotiktok:
        return snaptik(url).get_media()[0]

    @classmethod
    def get_video_url(cls, url: str) -> str:
        try:
            return cls.__get_video(url).json
        except InvalidUrl:
            raise TikTokInvalidUrl(url)
