from typing import Callable

from . import db
from services.schedule import Schedule


TASKS_ON_STARTUP_ASYNC = [
    db.on_startup(),
    Schedule.on_startup(),
]

TASKS_ON_STARTUP_SYNC: list[Callable[[], None]] = []
