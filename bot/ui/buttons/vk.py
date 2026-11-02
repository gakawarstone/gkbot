from dataclasses import dataclass
from enum import Enum

from aiogram.types import InlineKeyboardButton

from utils.vk import VKReference, parse_vk_reference

PREFIX = "vkbtn"
_MAX_CALLBACK_BYTES = 64
_MESSAGE_REFERENCE = "~"


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
    reference: VKReference
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
        payload = base + (
            f"{callback_data.use_callback_message_as_status}:"
            f"{callback_data.reference.value}"
        )
        if len(payload.encode("utf-8")) <= _MAX_CALLBACK_BYTES:
            return payload
        if not callback_data.use_callback_message_as_status:
            raise ValueError("VK callback data exceeds Telegram's 64-byte limit")
        return f"{base}True:{_MESSAGE_REFERENCE}"


class VKDownloadButtonCallbackDataDeserializer:
    @staticmethod
    def deserialize(
        callback_data: str, message_text: str | None = None
    ) -> VKDownloadButtonCallbackData:
        _, _, raw_status, raw_vk_id = callback_data.split(":", 3)
        use_callback_message_as_status = raw_status != "False"
        if raw_vk_id == _MESSAGE_REFERENCE:
            if raw_status != "True" or not message_text:
                raise ValueError("VK reference message is missing")
            reference = parse_vk_reference(message_text)
        else:
            reference = parse_vk_reference(raw_vk_id)
        return VKDownloadButtonCallbackData(reference, use_callback_message_as_status)


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
