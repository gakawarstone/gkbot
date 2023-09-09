from aiogram import Router

from . import tiktok
from . import ytdlp
from . import jutsu
from . import ytdlp_short
from . import instagram


def setup(r: Router):
    tiktok.setup(r)
    ytdlp.setup(r)
    jutsu.setup(r)
    ytdlp_short.setup(r)
    instagram.setup(r)
