from aiogram import Router

from . import tiktok
from . import ytdlp
from . import jutsu


def setup(r: Router):
    tiktok.setup(r)
    ytdlp.setup(r)
    jutsu.setup(r)
