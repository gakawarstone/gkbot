from dataclasses import dataclass

from aiogram.types import InlineKeyboardButton

PREFIX = "matreshkabtn"


@dataclass(frozen=True, slots=True)
class MatreshkaDownloadButtonCallbackData:
    video_id: str


class MatreshkaDownloadButtonCallbackDataSerializer:
    @staticmethod
    def serialize(callback_data: MatreshkaDownloadButtonCallbackData) -> str:
        return f"{PREFIX}:{callback_data.video_id}"


class MatreshkaDownloadButtonCallbackDataDeserializer:
    @staticmethod
    def deserialize(callback_data: str) -> MatreshkaDownloadButtonCallbackData:
        prefix, video_id = callback_data.split(":", maxsplit=1)
        if prefix != PREFIX or not video_id:
            raise ValueError("Invalid Matreshka download callback data")

        return MatreshkaDownloadButtonCallbackData(video_id)


class MatreshkaDownloadButtonBuilder:
    @staticmethod
    def build(
        callback_data: MatreshkaDownloadButtonCallbackData,
    ) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text="Аудио",
            callback_data=MatreshkaDownloadButtonCallbackDataSerializer.serialize(
                callback_data
            ),
        )
