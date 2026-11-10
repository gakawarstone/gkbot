from typing import Any, cast

from extensions.handlers.context_manager import (
    BaseContext,
    BaseContextManager,
    ContextField,
)


class RoadSettingsContext(BaseContext):
    setting_name = ContextField(str)
    setting_new_value = ContextField(cast(type[Any], Any))


class RoadSettingsContextManager(BaseContextManager[RoadSettingsContext]):
    props = RoadSettingsContext
