from aiogram.types import Message

from extensions.handlers.context_manager import (
    BaseContext,
    BaseContextManager,
    ContextField,
)


class _AddBookContext(BaseContext):
    name = ContextField(str)
    author = ContextField(str)
    chapter_cnt = ContextField(int)
    message = ContextField(Message)


class AddBookContextManager(BaseContextManager[_AddBookContext]):
    props = _AddBookContext
