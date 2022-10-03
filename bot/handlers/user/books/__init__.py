from aiogram import Router

from . import menu
from . import callbacks
from . import messages


def setup(r: Router):
    menu.setup(r)
    callbacks.setup(r)
    messages.setup(r)
