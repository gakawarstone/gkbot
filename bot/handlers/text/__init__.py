from aiogram import Router

from . import tiktok
from . import ytdlp
from . import jutsu
from . import shorts


def setup(r: Router):
    tiktok.setup(r)
    ytdlp.setup(r)
    jutsu.setup(r)
    shorts.setup(r)
