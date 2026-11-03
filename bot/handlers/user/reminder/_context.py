from dataclasses import dataclass
from datetime import date as date_type
from datetime import time as time_type
from datetime import timedelta
from enum import StrEnum, auto
from typing import Optional

from aiogram.types import Message

from extensions.handlers.context_manager import BaseContext, BaseContextManager


@dataclass
class _ReminderContext(BaseContext):
    text: Optional[str] = None
    tz: Optional[timedelta] = None
    date: Optional[date_type] = None
    time: Optional[time_type] = None
    message: Optional[Message] = None


class _ReminderKeys(StrEnum):
    text = auto()
    tz = auto()
    date = auto()
    time = auto()
    message = auto()


class ReminderContextManager(BaseContextManager[_ReminderContext, _ReminderKeys]):
    props = _ReminderContext
    keys: type[_ReminderKeys] = _ReminderKeys
