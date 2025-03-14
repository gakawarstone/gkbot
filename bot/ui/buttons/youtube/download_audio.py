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
class YoutubeDownloadAudioButtonData(_Data):
    event: str = "dlmp3"
    text: str = "Аудио"


class YoutubeDownloadAudioButtonCallbackData(_CallbackData):
    pass


class YoutubeDownloadAudioButtonDataSerializer(
    _DataSerializer[YoutubeDownloadAudioButtonData]
):
    pass


class YoutubeDownloadAudioButtonCallbackDataSerializer(
    _CallbackDataSerializer[
        YoutubeDownloadAudioButtonData, YoutubeDownloadAudioButtonCallbackData
    ]
):
    pass


class YoutubeDownloadAudioButtonCallbackDataDeserializer(
    _CallbackDataDeserializer[YoutubeDownloadAudioButtonCallbackData]
):
    _callback_data_type = YoutubeDownloadAudioButtonCallbackData


class YoutubeDownloadAudioButtonBuilder(
    _Builder[YoutubeDownloadAudioButtonData, YoutubeDownloadAudioButtonCallbackData]
):
    pass
