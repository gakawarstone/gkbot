from core.types import StartupHook
from services.gkfeed.api import GkfeedApi
from services.schedule import Schedule

from . import db

STARTUP_HOOKS: tuple[StartupHook, ...] = (
    db.on_startup,
    Schedule.on_startup,
    GkfeedApi.on_startup,
)
