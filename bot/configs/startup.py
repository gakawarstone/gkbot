import models
from services.schedule import Schedule
from .db import DB_URL, MODELS


TASKS_ON_STARTUP_ASYNC = [
    models.setup(DB_URL, MODELS),
    Schedule.on_startup(),
]

TASKS_ON_STARTUP_SYNC = []
