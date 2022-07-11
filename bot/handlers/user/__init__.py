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


def setup(mng: BotManager):
    tts.setup(mng)
    tasks.setup(mng)
    braintrash.setup(mng)
    bomber.setup(mng)
    reminder.setup(mng)
    road.setup(mng)
    wiki.setup(mng)
    shiki.setup(mng)
    adm.setup(mng)