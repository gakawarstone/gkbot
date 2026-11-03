from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Optional

from aiogram.types import Message

from extensions.handlers.context_manager import BaseContext, BaseContextManager


@dataclass
class _AddBookContext(BaseContext):
    name: Optional[str] = None
    author: Optional[str] = None
    chapter_cnt: Optional[int] = None
    message: Optional[Message] = None


class _AddBookKeys(StrEnum):
    book_name = "name"
    author = auto()
    chapter_cnt = auto()
    message = auto()


class AddBookContextManager(BaseContextManager[_AddBookContext, _AddBookKeys]):
    props = _AddBookContext
    keys: type[_AddBookKeys] = _AddBookKeys
