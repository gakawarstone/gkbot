from aiogram import Router

from . import youtube
from . import delete_message


def setup(r: Router):
    youtube.setup(r)
    delete_message.setup(r)
