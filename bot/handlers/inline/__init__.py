from aiogram import Router

from . import tiktok, youtube


def setup(r: Router):
    tiktok.setup(r)
    youtube.setup(r)
