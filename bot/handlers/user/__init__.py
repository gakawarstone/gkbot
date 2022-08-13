from lib.bot import BotManager
from . import text_to_speech as tts
from . import tasks
from . import braintrash
from . import bomber
from . import reminder
from . import road_to_the_dream as road
from . import wiki
from . import shiki
from . import admins as adm
from . import timer


def setup(mng: BotManager):
    tts.setup(mng)  # NOTE dp.include_router(tts.router)?
    tasks.setup(mng)
    braintrash.setup(mng)
    bomber.setup(mng)
    reminder.setup(mng)
    road.setup(mng)
    wiki.setup(mng)
    shiki.setup(mng)
    adm.setup(mng)
    timer.setup(mng)
