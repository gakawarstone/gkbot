from dataclasses import dataclass
from typing import Optional, Any


from contrib.handlers.message.context_manager import BaseContextManager, BaseContext


@dataclass
class RoadSettingsContext(BaseContext):
    setting_name: Optional[str] = None
    setting_new_value: Optional[Any] = None


class RoadSettingsContextManager(BaseContextManager[RoadSettingsContext]):
    props = RoadSettingsContext
