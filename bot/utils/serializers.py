from aiogram.types import InlineQueryResultVideo, InputMediaVideo


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
        thumb_url=video_url,
        input_message_content=InputMediaVideo(
            type='video',
            media=video_url,
        )
    )
