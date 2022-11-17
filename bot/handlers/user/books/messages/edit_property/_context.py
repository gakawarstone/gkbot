from abc import ABC
from typing import Optional
from dataclasses import dataclass

from contrib.handlers.message.context_manager import (BaseContextManager,
                                                      Property)


class _Properties:
    property_name = Property('book_property_name', str)
    new_value = Property('new_val', str)
    book_id = Property('book_id', int)


@dataclass
class _EditBookPropertyContext:
    property_name: Optional[_Properties.property_name.type]
    new_value: Optional[_Properties.new_value.type]
    book_id: Optional[_Properties.book_id.type]


class EditBookPropertyContextManager(BaseContextManager, ABC):
    props: _Properties = _Properties
    _context_type = _EditBookPropertyContext

    @property
    def ctx(self) -> _EditBookPropertyContext:
        return super().ctx
