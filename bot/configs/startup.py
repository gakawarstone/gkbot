from models import setup
from . import db
from services.schedule import Schedule


TASKS_ON_STARTUP_ASYNC = [
    setup(DB_URL, MODELS),
    db.on_startup(),
    Schedule.on_startup(),
]

TASKS_ON_STARTUP_SYNC = []
