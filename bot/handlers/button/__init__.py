from aiogram import Router

from . import youtube
from . import delete_message
from . import vk
from . import pornhub


def setup(r: Router):
    youtube.setup(r)
    delete_message.setup(r)
    vk.setup(r)
    pornhub.setup(r)

