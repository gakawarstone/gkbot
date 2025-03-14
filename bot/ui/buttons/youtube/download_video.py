from dataclasses import dataclass

from . import (
    BaseButtonData as _Data,
    BaseButtonCallbackData as _CallbackData,
    BaseButtonDataSerializer as _DataSerializer,
    BaseButtonCallbackDataSerializer as _CallbackDataSerializer,
    BaseButtonCallbackDataDeserializer as _CallbackDataDeserializer,
    BaseButtonBuilder as _Builder,
)


@dataclass
class YoutubeDownloadVideoButtonData(_Data):
    event: str = "dlmp4"
    text: str = "Видео"


class YoutubeDownloadVideoButtonDataSerializer(
    _DataSerializer[YoutubeDownloadVideoButtonData]
):
    pass


class YoutubeDownloadVideoButtonCallbackData(_CallbackData):
    pass


class YoutubeDownloadVideoButtonCallbackDataSerializer(
    _CallbackDataSerializer[
        YoutubeDownloadVideoButtonData, YoutubeDownloadVideoButtonCallbackData
    ]
):
    pass


class YoutubeDownloadVideoButtonCallbackDataDeserializer(
    _CallbackDataDeserializer[YoutubeDownloadVideoButtonCallbackData]
):
    _callback_data_type = YoutubeDownloadVideoButtonCallbackData


class YoutubeDownloadVideoButtonBuilder(
    _Builder[YoutubeDownloadVideoButtonData, YoutubeDownloadVideoButtonCallbackData]
):
    pass
