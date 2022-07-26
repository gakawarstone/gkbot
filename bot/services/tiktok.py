from io import BytesIO

from aiogram.types import BufferedInputFile, InlineQueryResultVideo, InputMediaVideo

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
    def __get_video_url(cls, url: str) -> str:
        return snaptik(url).get_media()[0].json

    @classmethod
    def __to_query_result(cls, title: str, description: str, video_url: str) -> InlineQueryResultVideo:
        return InlineQueryResultVideo(
            id='tik',
            type='video',
            title=title,
            description=description,
            video_url=video_url,
            mime_type='video/mp4',
            thumb_url=video_url,
            input_message_content=InputMediaVideo(
                type='video',
                media=video_url,
            )
        )

    @classmethod
    def get_as_query_result(cls, url: str) -> InlineQueryResultVideo:
        return cls.__to_query_result('TikTok', 'tap to send', cls.__get_video_url(url))

    @classmethod
    def download_as_input_file(cls, url: str) -> BufferedInputFile:
        try:
            return BufferedInputFile(
                cls.__download_video(url).getvalue(), 'video.mp4')
        except InvalidUrl:
            raise TikTokInvalidUrl(url)
