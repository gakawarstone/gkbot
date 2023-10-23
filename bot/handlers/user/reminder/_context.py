from dataclasses import dataclass
from datetime import timedelta
from datetime import date as date_type
from datetime import time as time_type
from typing import Optional

from aiogram.types import Message

from extensions.handlers.message.context_manager import BaseContextManager, BaseContext


@dataclass
class _ReminderContext(BaseContext):
    text: Optional[str] = None
    tz: Optional[timedelta] = None
    date: Optional[date_type] = None
    time: Optional[time_type] = None
    message: Optional[Message] = None


class ReminderContextManager(BaseContextManager[_ReminderContext]):
    props = _ReminderContext
