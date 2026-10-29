from dataclasses import dataclass
from datetime import date as date_type
from datetime import time as time_type
from datetime import timedelta

from aiogram.types import Message

from extensions.handlers.context_manager import BaseContext, BaseContextManager


@dataclass
class _ReminderContext(BaseContext):
    text: str | None = None
    tz: timedelta | None = None
    date: date_type | None = None
    time: time_type | None = None
    message: Message | None = None


class ReminderContextManager(BaseContextManager[_ReminderContext]):
    props = _ReminderContext
