from dataclasses import dataclass
from enum import Enum

from aiogram.types import InlineKeyboardButton

PREFIX = "vkbtn"
_MAX_CALLBACK_BYTES = 64


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
    vk_id: str = ""
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
        if callback_data.use_callback_message_as_status:
            return base
        if not callback_data.vk_id:
            raise ValueError("VK video identifier is missing")
        payload = f"{base}False:{callback_data.vk_id}"
        if len(payload.encode("utf-8")) > _MAX_CALLBACK_BYTES:
            raise ValueError("VK callback data exceeds Telegram's 64-byte limit")
        return payload


class VKDownloadButtonCallbackDataDeserializer:
    @staticmethod
    def deserialize(callback_data: str) -> VKDownloadButtonCallbackData:
        _, _, raw_status, *values = callback_data.split(":", 3)
        if not raw_status:
            return VKDownloadButtonCallbackData(use_callback_message_as_status=True)
        if not values or not values[0]:
            raise ValueError("VK callback reference is missing")
        return VKDownloadButtonCallbackData(values[0], raw_status != "False")


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
