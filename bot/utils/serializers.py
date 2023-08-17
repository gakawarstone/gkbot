from aiogram.types import InlineQueryResultVideo


def url_to_video_query_result(
        video_url: str, title: str,
        description: str, id: str = 'video') -> InlineQueryResultVideo:
    return InlineQueryResultVideo(
        id=id,
        type='video',
        title=title,
        description=description,
        video_url=video_url,
        mime_type='video/mp4',
        thumbnail_url=video_url,
        thumb_url=video_url,
    )
