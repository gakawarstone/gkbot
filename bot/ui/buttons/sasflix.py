from dataclasses import dataclass

from aiogram.types import InlineKeyboardButton

PREFIX = "sasflixbtn"


@dataclass(frozen=True, slots=True)
class SasflixDownloadButtonCallbackData:
    topic_uuid: str


class SasflixDownloadButtonCallbackDataSerializer:
    @staticmethod
    def serialize(callback_data: SasflixDownloadButtonCallbackData) -> str:
        return f"{PREFIX}:{callback_data.topic_uuid}"


class SasflixDownloadButtonCallbackDataDeserializer:
    @staticmethod
    def deserialize(callback_data: str) -> SasflixDownloadButtonCallbackData:
        prefix, topic_uuid = callback_data.split(":", maxsplit=1)
        if prefix != PREFIX or not topic_uuid:
            raise ValueError("Invalid Sasflix download callback data")

        return SasflixDownloadButtonCallbackData(topic_uuid)


class SasflixDownloadButtonBuilder:
    @staticmethod
    def build(
        callback_data: SasflixDownloadButtonCallbackData,
    ) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text="Аудио",
            callback_data=SasflixDownloadButtonCallbackDataSerializer.serialize(
                callback_data
            ),
        )
