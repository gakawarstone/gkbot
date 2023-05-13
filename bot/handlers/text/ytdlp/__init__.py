from aiogram import Router

from . import markup
from . import callback


def setup(r: Router):
    markup.setup(r)
    callback.setup(r)
