from aiogram import Router

from . import tiktok
from . import youtube


def setup(r: Router):
    tiktok.setup(r)
    youtube.setup(r)
