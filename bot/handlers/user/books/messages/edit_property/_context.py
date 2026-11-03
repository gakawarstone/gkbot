from abc import ABC
from dataclasses import dataclass
from typing import Optional

from extensions.handlers.context_manager import BaseContext, BaseContextManager


@dataclass
class _EditBookPropertyContext(BaseContext):
    property_name: Optional[str] = None
    new_value: Optional[str] = None
    book_id: Optional[int] = None


class EditBookPropertyContextManager(BaseContextManager[_EditBookPropertyContext], ABC):
    props = _EditBookPropertyContext
