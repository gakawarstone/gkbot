from abc import ABC
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Optional

from extensions.handlers.context_manager import BaseContext, BaseContextManager


@dataclass
class _EditBookPropertyContext(BaseContext):
    property_name: Optional[str] = None
    new_value: Optional[str] = None
    book_id: Optional[int] = None


class _EditBookPropertyKeys(StrEnum):
    property_name = auto()
    new_value = auto()
    book_id = auto()


class EditBookPropertyContextManager(
    BaseContextManager[_EditBookPropertyContext, _EditBookPropertyKeys], ABC
):
    props = _EditBookPropertyContext
    keys: type[_EditBookPropertyKeys] = _EditBookPropertyKeys
