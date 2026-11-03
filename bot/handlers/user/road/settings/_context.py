from dataclasses import dataclass
from typing import Any, Optional

from extensions.handlers.context_manager import BaseContext, BaseContextManager


@dataclass
class RoadSettingsContext(BaseContext):
    setting_name: Optional[str] = None
    setting_new_value: Optional[Any] = None


class RoadSettingsContextManager(BaseContextManager[RoadSettingsContext]):
    props = RoadSettingsContext
