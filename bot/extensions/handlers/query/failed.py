from typing import Type, Callable
from functools import wraps

from aiogram.types import InputTextMessageContent, InlineQueryResultArticle, InlineQuery


def get_failed_result(query: InlineQuery, message_to_send: str, description: str):
    return InlineQueryResultArticle(
        id=query.query,
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
                return [get_failed_result(query, message_to_send, description)]

        return wrapper

    return decorator
