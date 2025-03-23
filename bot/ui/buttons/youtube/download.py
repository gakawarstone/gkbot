from dataclasses import dataclass
from enum import Enum

from aiogram.types import InlineKeyboardButton

PREFIX = "ytbtn"


@dataclass
class _BaseYoutubeDownloadButtonData:
    event: str
    text: str
    prefix: str = PREFIX


@dataclass
class _YoutubeDownloadAudioButtonData(_BaseYoutubeDownloadButtonData):
    event: str = "dlmp3"
    text: str = "Аудио"


@dataclass
class _YoutubeDownloadVideoButtonData(_BaseYoutubeDownloadButtonData):
    event: str = "dlmp4"
    text: str = "Видео"


class YoutubeDownloadButtonData(Enum):
    audio = _YoutubeDownloadAudioButtonData()
    video = _YoutubeDownloadVideoButtonData()


@dataclass
class YoutubeDownloadButtonCallbackData:
    yt_video_code: str
    use_callback_message_as_status: bool = False


class YoutubeDownloadButtonDataSerializer:
    @staticmethod
    def get_full_prefix(
        button_data: YoutubeDownloadButtonData,
    ) -> str:
        data = button_data.value
        return f"{data.prefix}:{data.event}:"


class YoutubeDownloadButtonCallbackDataSerializer:
    @staticmethod
    def serialize(
        button_data: YoutubeDownloadButtonData,
        callback_data: YoutubeDownloadButtonCallbackData,
    ) -> str:
        base = YoutubeDownloadButtonDataSerializer.get_full_prefix(button_data)
        return base + (
            f"{callback_data.use_callback_message_as_status}:"
            f"{callback_data.yt_video_code}"
        )


class YoutubeDownloadButtonCallbackDataDeserializer:
    @staticmethod
    def deserialize(callback_data: str) -> YoutubeDownloadButtonCallbackData:
        _, _, raw_status, raw_code = callback_data.split(":")
        yt_video_code = raw_code
        use_callback_message_as_status = raw_status != "False"
        return YoutubeDownloadButtonCallbackData(
            yt_video_code, use_callback_message_as_status
        )


class YoutubeDownloadButtonBuilder:
    @staticmethod
    def build(
        button_data: YoutubeDownloadButtonData,
        callback_data: YoutubeDownloadButtonCallbackData,
    ) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=button_data.value.text,
            callback_data=YoutubeDownloadButtonCallbackDataSerializer.serialize(
                button_data, callback_data
            ),
        )
