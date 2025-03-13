from dataclasses import dataclass

from aiogram.utils.keyboard import InlineKeyboardButton


@dataclass
class YoutubeDownloadAudioButtonData:
    prefix: str = "ytbtn"
    event: str = "dlmp3"
    text: str = "Аудио"


@dataclass
class YoutubeDownloadAudioButtonCallbackData:
    yt_video_code: str
    use_callback_message_as_status: bool = True


class YoutubeDownloadAudioButtonDataSerializer:
    @staticmethod
    def get_full_prefix(
        button_data: YoutubeDownloadAudioButtonData,
    ) -> str:
        return f"{button_data.prefix}:{button_data.event}:"


class YoutubeDownloadAudioButtonCallbackDataSerializer:
    @staticmethod
    def serialize(
        button_data: YoutubeDownloadAudioButtonData,
        callback_data: YoutubeDownloadAudioButtonCallbackData,
    ) -> str:
        base = YoutubeDownloadAudioButtonDataSerializer.get_full_prefix(button_data)
        return base + (
            f"{callback_data.use_callback_message_as_status}:"
            f"{callback_data.yt_video_code}"
        )


class YoutubeDownloadAudioButtonCallbackDataDeserializer:
    @staticmethod
    def deserialize(callback_data: str) -> YoutubeDownloadAudioButtonCallbackData:
        _, _, use_callback_message_as_status, yt_video_code = callback_data.split(":")
        return YoutubeDownloadAudioButtonCallbackData(
            yt_video_code, bool(use_callback_message_as_status)
        )


class YoutubeDownloadAudioButtonBuilder:
    @staticmethod
    def build(
        button_data: YoutubeDownloadAudioButtonData,
        callback_data: YoutubeDownloadAudioButtonCallbackData,
    ) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=button_data.text,
            callback_data=YoutubeDownloadAudioButtonCallbackDataSerializer.serialize(
                button_data, callback_data
            ),
        )
