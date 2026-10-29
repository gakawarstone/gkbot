from dataclasses import dataclass

from aiogram.types import Message

from extensions.handlers.context_manager import BaseContext, BaseContextManager


@dataclass
class _AddBookContext(BaseContext):
    name: str | None = None
    author: str | None = None
    chapter_cnt: int | None = None
    message: Message | None = None


class AddBookContextManager(BaseContextManager[_AddBookContext]):
    props = _AddBookContext
