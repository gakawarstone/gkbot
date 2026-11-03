from typing import Any

from extensions.handlers.context_manager import (
    BaseContext,
    BaseContextManager,
    ContextField,
)


class RoadSettingsContext(BaseContext):
    setting_name = ContextField[str](str)
    setting_new_value = ContextField[Any](Any)


class RoadSettingsContextManager(BaseContextManager[RoadSettingsContext]):
    props = RoadSettingsContext
