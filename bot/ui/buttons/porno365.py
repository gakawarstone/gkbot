from dataclasses import dataclass
from enum import Enum

from aiogram.types import InlineKeyboardButton

PREFIX = "p365btn"


@dataclass
class _BasePorno365DownloadButtonData:
    event: str
    text: str
    prefix: str = PREFIX


@dataclass
class _Porno365DownloadVideoButtonData(_BasePorno365DownloadButtonData):
    event: str = "dlmp4"
    text: str = "Видео"


class Porno365DownloadButtonData(Enum):
    video = _Porno365DownloadVideoButtonData()


@dataclass
class Porno365DownloadButtonCallbackData:
    page_url: str
    use_callback_message_as_status: bool = False


class Porno365DownloadButtonDataSerializer:
    @staticmethod
    def get_full_prefix(button_data: Porno365DownloadButtonData) -> str:
        data = button_data.value
        return f"{data.prefix}:{data.event}:"


class Porno365DownloadButtonCallbackDataSerializer:
    @staticmethod
    def serialize(
        button_data: Porno365DownloadButtonData,
        callback_data: Porno365DownloadButtonCallbackData,
    ) -> str:
        base = Porno365DownloadButtonDataSerializer.get_full_prefix(button_data)
        return base + (
            f"{callback_data.use_callback_message_as_status}:"
            f"{callback_data.page_url}"
        )


class Porno365DownloadButtonCallbackDataDeserializer:
    @staticmethod
    def deserialize(callback_data: str) -> Porno365DownloadButtonCallbackData:
        _, _, raw_status, raw_url = callback_data.split(":", 3)
        use_callback_message_as_status = raw_status != "False"
        return Porno365DownloadButtonCallbackData(raw_url, use_callback_message_as_status)


class Porno365DownloadButtonBuilder:
    @staticmethod
    def build(
        button_data: Porno365DownloadButtonData,
        callback_data: Porno365DownloadButtonCallbackData,
    ) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=button_data.value.text,
            callback_data=Porno365DownloadButtonCallbackDataSerializer.serialize(
                button_data, callback_data
            ),
        )
