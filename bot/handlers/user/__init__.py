from lib.bot import BotManager
from . import text_to_speech as tts


def setup(mng: BotManager):
    tts.setup(mng)
