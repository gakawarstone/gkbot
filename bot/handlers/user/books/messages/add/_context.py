from typing import Optional
from dataclasses import dataclass

from contrib.handlers.message.context_manager import BaseContextManager, Property


class _Properties:
    name = Property('name', str)
    author = Property('author', str)
    chapter_cnt = Property('ch_cnt', int)


@dataclass
class _AddBookContext:
    name: Optional[_Properties.name.type]
    author: Optional[_Properties.author.type]
    chapter_cnt: Optional[_Properties.chapter_cnt.type]


class AddBookContextManager(BaseContextManager):
    props: _Properties = _Properties
    _context_type = _AddBookContext

    @property
    def ctx(self) -> _AddBookContext:
        return super().ctx
