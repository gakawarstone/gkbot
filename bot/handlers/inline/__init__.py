from aiogram import Router

from . import tiktok, youtube, chance


def setup(r: Router):
    tiktok.setup(r)
    youtube.setup(r)
    chance.setup(r)
