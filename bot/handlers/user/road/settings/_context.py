from dataclasses import dataclass
from typing import Any

from extensions.handlers.context_manager import BaseContext, BaseContextManager


@dataclass
class RoadSettingsContext(BaseContext):
    setting_name: str | None = None
    setting_new_value: Any | None = None


class RoadSettingsContextManager(BaseContextManager[RoadSettingsContext]):
    props = RoadSettingsContext
