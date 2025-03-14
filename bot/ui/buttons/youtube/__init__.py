from dataclasses import dataclass
from typing import Type

from aiogram.utils.keyboard import InlineKeyboardButton


@dataclass
class BaseButtonData:
    event: str
    text: str
    prefix: str = "ytbtn"


@dataclass
class BaseButtonCallbackData:
    yt_video_code: str
    use_callback_message_as_status: bool = True


class BaseButtonDataSerializer[T: BaseButtonData]:
    @staticmethod
    def get_full_prefix(
        button_data: T,
    ) -> str:
        return f"{button_data.prefix}:{button_data.event}:"


class BaseButtonCallbackDataSerializer[T: BaseButtonData, S: BaseButtonCallbackData]:
    @staticmethod
    def serialize(
        button_data: T,
        callback_data: S,
    ) -> str:
        base = BaseButtonDataSerializer.get_full_prefix(button_data)
        return base + (
            f"{callback_data.use_callback_message_as_status}:"
            f"{callback_data.yt_video_code}"
        )


class BaseButtonCallbackDataDeserializer[T: BaseButtonCallbackData]:
    _callback_data_type: Type[T]

    @classmethod
    def deserialize(cls, callback_data: str) -> T:
        _, _, use_callback_message_as_status, yt_video_code = callback_data.split(":")
        return cls._callback_data_type(
            yt_video_code, bool(use_callback_message_as_status)
        )


class BaseButtonBuilder[T: BaseButtonData, S: BaseButtonCallbackData]:
    @staticmethod
    def build(
        button_data: T,
        callback_data: S,
    ) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=button_data.text,
            callback_data=BaseButtonCallbackDataSerializer.serialize(
                button_data, callback_data
            ),
        )
