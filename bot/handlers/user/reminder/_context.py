from dataclasses import dataclass
from datetime import date, time, timedelta
from typing import Optional, Type

from aiogram.types import Message

from contrib.handlers.message.context_manager import BaseContextManager, BaseContext


@dataclass
class _ReminderContext(BaseContext):
    text: Optional[str] = None
    tz: Optional[timedelta] = None
    date: Optional[date] = None
    time: Optional[time] = None
    message: Optional[Message] = None


class ReminderContextManager(BaseContextManager[_ReminderContext]):
    props = _ReminderContext
