from aiogram import Router

from . import tiktok
from . import youtube
from . import jutsu


def setup(r: Router):
    tiktok.setup(r)
    youtube.setup(r)
    jutsu.setup(r)
