from aiogram import Router

from . import feed


def setup(r: Router):
    feed.setup(r)
