from aiogram.types import Message

from extensions.handlers.context_manager import (
    BaseContext,
    BaseContextManager,
    ContextField,
)


class _AddBookContext(BaseContext):
    name = ContextField[str](str)
    author = ContextField[str](str)
    chapter_cnt = ContextField[int](int)
    message = ContextField[Message](Message)


class AddBookContextManager(BaseContextManager[_AddBookContext]):
    props = _AddBookContext
