from typing import Optional
from dataclasses import dataclass

from aiogram.types import Message

from contrib.handlers.message.context_manager import BaseContextManager, BaseContext


@dataclass
class _AddBookContext(BaseContext):
    name: Optional[str] = None
    author: Optional[str] = None
    chapter_cnt: Optional[int] = None
    message: Optional[Message] = None


class AddBookContextManager(BaseContextManager[_AddBookContext]):
    props = _AddBookContext
