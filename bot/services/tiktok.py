from dataclasses import dataclass
import requests


@dataclass
class InfoVideoTikTok:
    video_url: str
    music_url: str


def info_video_tiktok_serializer(data: dict) -> InfoVideoTikTok:
    return InfoVideoTikTok(
        video_url=data['nwm_video_url'],
        music_url=data['video_music_url']
    )


class TikTokInvalidUrl(Exception):
    def __init__(self, url: str) -> None:
        self.url = url

    def __str__(self) -> str:
        return f'Invalid TikTok video url {self.url}'


class TikTokDownloader:
    @classmethod
    def __get_video_info(cls, url: str) -> InfoVideoTikTok:
        try:
            return info_video_tiktok_serializer(
                requests.get(f'https://api.douyin.wtf/api?url={url}').json()
            )
        except KeyError:
            raise TikTokInvalidUrl(url)

    @classmethod
    def get_video_url(cls, url: str) -> str:
        return cls.__get_video_info(url).video_url
