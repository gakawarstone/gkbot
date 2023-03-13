from typing import Optional
from dataclasses import dataclass

from contrib.handlers.message.context_manager import BaseContextManager, BaseContext


@dataclass
class _AddBookContext(BaseContext):
    name: Optional[str] = None
    author: Optional[str] = None
    chapter_cnt: Optional[int] = None


class AddBookContextManager(BaseContextManager[_AddBookContext]):
    props = _AddBookContext
