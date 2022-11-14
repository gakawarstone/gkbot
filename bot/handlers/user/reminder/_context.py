from datetime import date, time, timedelta
from dataclasses import dataclass
from typing import Optional

from aiogram.types import Message

from contrib.handlers.message.context_manager import BaseContextManager, Property


class _Properties:
    text = Property('text', str)
    tz = Property('tz', timedelta)
    date = Property('date', date)
    time = Property('time', time)
    message = Property('mes', Message)


@dataclass
class _ReminderContext:
    text: Optional[_Properties.text.type]
    tz: Optional[_Properties.tz.type]
    date: Optional[_Properties.date.type]
    time: Optional[_Properties.time.type]
    message: Optional[_Properties.message.type]


class ReminderContextManager(BaseContextManager):
    props = _Properties
    _context_type = _ReminderContext
