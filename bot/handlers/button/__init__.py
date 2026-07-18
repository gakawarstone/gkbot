from aiogram import Router

from . import youtube
from . import delete_message
from . import vk
from . import pornhub
from . import porno365
from . import sasflix


def setup(r: Router):
    youtube.setup(r)
    delete_message.setup(r)
    vk.setup(r)
    pornhub.setup(r)
    porno365.setup(r)
    sasflix.setup(r)
