from aiogram import Router

from . import callbacks, menu, messages


def setup(r: Router):
    menu.setup(r)
    callbacks.setup(r)
    messages.setup(r)
