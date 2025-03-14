from aiogram import Router

from . import youtube


def setup(r: Router):
    youtube.setup(r)
