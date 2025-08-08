from dataclasses import dataclass
from enum import Enum

from aiogram.types import InlineKeyboardButton

PREFIX = "vkbtn"


@dataclass
class _BaseVKDownloadButtonData:
    event: str
    text: str
    prefix: str = PREFIX


@dataclass
class _VKDownloadAudioButtonData(_BaseVKDownloadButtonData):
    event: str = "dlmp3"
    text: str = "Аудио"


@dataclass
class _VKDownloadVideoButtonData(_BaseVKDownloadButtonData):
    event: str = "dlmp4"
    text: str = "Видео"


class VKDownloadButtonData(Enum):
    audio = _VKDownloadAudioButtonData()
    video = _VKDownloadVideoButtonData()


@dataclass
class VKDownloadButtonCallbackData:
    url: str
    use_callback_message_as_status: bool = False


class VKDownloadButtonDataSerializer:
    @staticmethod
    def get_full_prefix(
        button_data: VKDownloadButtonData,
    ) -> str:
        data = button_data.value
        return f"{data.prefix}:{data.event}:"


class VKDownloadButtonCallbackDataSerializer:
    @staticmethod
    def serialize(
        button_data: VKDownloadButtonData,
        callback_data: VKDownloadButtonCallbackData,
    ) -> str:
        base = VKDownloadButtonDataSerializer.get_full_prefix(button_data)
        return base + (
            f"{callback_data.use_callback_message_as_status}:"
            f"{callback_data.url}"
        )


class VKDownloadButtonCallbackDataDeserializer:
    @staticmethod
    def deserialize(callback_data: str) -> VKDownloadButtonCallbackData:
        _, _, raw_status, raw_url = callback_data.split(":", 3)
        url = raw_url
        use_callback_message_as_status = raw_status != "False"
        return VKDownloadButtonCallbackData(
            url, use_callback_message_as_status
        )


class VKDownloadButtonBuilder:
    @staticmethod
    def build(
        button_data: VKDownloadButtonData,
        callback_data: VKDownloadButtonCallbackData,
    ) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=button_data.value.text,
            callback_data=VKDownloadButtonCallbackDataSerializer.serialize(
                button_data, callback_data
            ),
        )
