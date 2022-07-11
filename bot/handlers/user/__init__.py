from lib.bot import BotManager
from . import text_to_speech as tts
from . import tasks


def setup(mng: BotManager):
    tts.setup(mng)
    tasks.setup(mng)
