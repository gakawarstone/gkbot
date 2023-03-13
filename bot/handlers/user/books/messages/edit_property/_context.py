from abc import ABC
from typing import Optional
from dataclasses import dataclass

from contrib.handlers.message.context_manager import BaseContextManager, BaseContext


@dataclass
class _EditBookPropertyContext(BaseContext):
    property_name: Optional[str] = None
    new_value: Optional[str] = None
    book_id: Optional[int] = None


class EditBookPropertyContextManager(BaseContextManager[_EditBookPropertyContext], ABC):
    props = _EditBookPropertyContext
