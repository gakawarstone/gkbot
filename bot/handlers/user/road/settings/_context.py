from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Any, Optional

from extensions.handlers.context_manager import BaseContext, BaseContextManager


@dataclass
class RoadSettingsContext(BaseContext):
    setting_name: Optional[str] = None
    setting_new_value: Optional[Any] = None


class _RoadSettingsKeys(StrEnum):
    setting_name = auto()
    setting_new_value = auto()


class RoadSettingsContextManager(
    BaseContextManager[RoadSettingsContext, _RoadSettingsKeys]
):
    props = RoadSettingsContext
    keys: type[_RoadSettingsKeys] = _RoadSettingsKeys
