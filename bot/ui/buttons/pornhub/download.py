from dataclasses import dataclass
from enum import Enum

from aiogram.types import InlineKeyboardButton

PREFIX = "phbtn"


@dataclass
class _BasePornhubDownloadButtonData:
    event: str
    text: str
    prefix: str = PREFIX


@dataclass
class _PornhubDownloadVideoButtonData(_BasePornhubDownloadButtonData):
    event: str = "dlmp4"
    text: str = "Видео"


class PornhubDownloadButtonData(Enum):
    video = _PornhubDownloadVideoButtonData()


@dataclass
class PornhubDownloadButtonCallbackData:
    ph_video_code: str
    use_callback_message_as_status: bool = False


class PornhubDownloadButtonDataSerializer:
    @staticmethod
    def get_full_prefix(
        button_data: PornhubDownloadButtonData,
    ) -> str:
        data = button_data.value
        return f"{data.prefix}:{data.event}:"


class PornhubDownloadButtonCallbackDataSerializer:
    @staticmethod
    def serialize(
        button_data: PornhubDownloadButtonData,
        callback_data: PornhubDownloadButtonCallbackData,
    ) -> str:
        base = PornhubDownloadButtonDataSerializer.get_full_prefix(button_data)
        return base + (
            f"{callback_data.use_callback_message_as_status}:"
            f"{callback_data.ph_video_code}"
        )


class PornhubDownloadButtonCallbackDataDeserializer:
    @staticmethod
    def deserialize(callback_data: str) -> PornhubDownloadButtonCallbackData:
        _, _, raw_status, raw_code = callback_data.split(":")
        ph_video_code = raw_code
        use_callback_message_as_status = raw_status != "False"
        return PornhubDownloadButtonCallbackData(
            ph_video_code, use_callback_message_as_status
        )


class PornhubDownloadButtonBuilder:
    @staticmethod
    def build(
        button_data: PornhubDownloadButtonData,
        callback_data: PornhubDownloadButtonCallbackData,
    ) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=button_data.value.text,
            callback_data=PornhubDownloadButtonCallbackDataSerializer.serialize(
                button_data, callback_data
            ),
        )
