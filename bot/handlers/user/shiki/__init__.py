from aiogram import Router

from . import updates, subs


def setup(r: Router):
    updates.setup(r)
    subs.setup(r)
