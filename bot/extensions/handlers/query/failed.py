import hashlib
from typing import Type, Callable
from functools import wraps

from aiogram.types import InputTextMessageContent, InlineQueryResultArticle, InlineQuery


def get_failed_result(query: InlineQuery, message_to_send: str, description: str):
    return InlineQueryResultArticle(
        id=hashlib.md5(query.query.encode()).hexdigest(),
        title="Failed",
        input_message_content=InputTextMessageContent(message_text=message_to_send),
        description=description,
    )


def async_return_failed_result_if(
    exceptions_to_handle: list[Type[BaseException]],
    message_to_send: str,
    description: str,
) -> Callable:
    def decorator(func: Callable) -> Callable[[InlineQuery], InlineQueryResultArticle]:
        @wraps(func)
        async def wrapper(
            query: InlineQuery, *args, **kwargs
        ) -> InlineQueryResultArticle:
            try:
                return await func(query, *args, **kwargs)
            except tuple(exceptions_to_handle):
                formatted_message = message_to_send.format(query.query)
                return [get_failed_result(query, formatted_message, description)]

        return wrapper

    return decorator
