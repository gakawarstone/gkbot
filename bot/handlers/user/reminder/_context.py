from datetime import date as date_type
from datetime import time as time_type
from datetime import timedelta

from aiogram.types import Message

from extensions.handlers.context_manager import (
    BaseContext,
    BaseContextManager,
    ContextField,
)


class _ReminderContext(BaseContext):
    text = ContextField[str](str)
    tz = ContextField[timedelta](timedelta)
    date = ContextField[date_type](date_type)
    time = ContextField[time_type](time_type)
    message = ContextField[Message](Message)


class ReminderContextManager(BaseContextManager[_ReminderContext]):
    props = _ReminderContext
