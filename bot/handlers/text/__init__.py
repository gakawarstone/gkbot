from aiogram import Router

from . import tiktok
from . import ytdlp
from . import jutsu
from . import ytdlp_short
from . import instagram
from . import tts


def setup(r: Router):
    tiktok.setup(r)
    ytdlp.setup(r)
    jutsu.setup(r)
    ytdlp_short.setup(r)
    instagram.setup(r)
    tts.setup(r)
