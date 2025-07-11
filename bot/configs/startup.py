from models import setup
from services.schedule import Schedule
from .db import DB_URL, MODELS


TASKS_ON_STARTUP_ASYNC = [
    setup(DB_URL, MODELS),
    Schedule.on_startup(),
]

TASKS_ON_STARTUP_SYNC = []
