from dataclasses import dataclass
from urllib.parse import urlparse
from uuid import UUID

from services.http import HttpService

_API_ROOT = "https://sasflix.ru/api/"


class InvalidSasflixTopicUrl(ValueError):
    """Raised when a URL does not identify a Sasflix topic."""


class SasflixAudioUnavailable(ValueError):
    """Raised when a Sasflix topic has no extracted audio track."""


@dataclass(frozen=True, slots=True)
class SasflixAudio:
    uuid: str
    title: str
    duration: int


class SasflixService:
    @staticmethod
    def get_topic_uuid(url: str) -> str:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip("/").split("/")
        if parsed_url.hostname != "sasflix.ru" or len(path_parts) != 2:
            raise InvalidSasflixTopicUrl(url)

        _, topic_uuid = path_parts
        try:
            UUID(topic_uuid)
        except ValueError:
            raise InvalidSasflixTopicUrl(url)

        return topic_uuid

    @classmethod
    async def get_audio(cls, topic_url: str) -> SasflixAudio:
        topic_uuid = cls.get_topic_uuid(topic_url)
        topic = await HttpService.get_json(_API_ROOT + f"web/topics/{topic_uuid}")

        content = topic.get("content")
        blocks = content.get("blocks", []) if isinstance(content, dict) else []
        for block in blocks:
            if not isinstance(block, dict) or block.get("type") != "video":
                continue

            video_data = block.get("data")
            if not isinstance(video_data, dict):
                continue

            audio_uuid = video_data.get("audio")
            if isinstance(audio_uuid, str) and audio_uuid:
                return SasflixAudio(
                    uuid=audio_uuid,
                    title=str(topic.get("title") or "Sasflix"),
                    duration=int(video_data.get("duration") or 0),
                )

        raise SasflixAudioUnavailable(topic_url)

    @staticmethod
    def get_audio_url(audio_uuid: str) -> str:
        return _API_ROOT + f"audio/{audio_uuid}"
