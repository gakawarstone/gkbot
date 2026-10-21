import hashlib

from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent


async def answer_article(
    query: InlineQuery,
    *,
    title: str,
    message_text: str,
    description: str,
    cache_time: int,
) -> bool:
    result = InlineQueryResultArticle(
        id=hashlib.md5(query.query.encode()).hexdigest(),
        title=title,
        input_message_content=InputTextMessageContent(message_text=message_text),
        description=description,
    )
    return await query.answer(
        results=[result],
        cache_time=cache_time,
        is_personal=False,
    )
