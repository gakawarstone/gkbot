from abc import ABC
from dataclasses import dataclass

from extensions.handlers.context_manager import BaseContextManager, BaseContext


@dataclass
class _EditBookPropertyContext(BaseContext):
    property_name: str | None = None
    new_value: str | None = None
    book_id: int | None = None


class EditBookPropertyContextManager(BaseContextManager[_EditBookPropertyContext], ABC):
    props = _EditBookPropertyContext
