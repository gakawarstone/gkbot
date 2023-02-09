from .types import InfoVideoTikTok
from .exceptions import SerializationError


def info_video_tiktok_serializer(data: dict) -> InfoVideoTikTok:
    try:
        return InfoVideoTikTok(
            video_url=data['video_data']['nwm_video_url'],
            music_url=data['music']['play_url']
        )
    except KeyError:
        raise SerializationError
