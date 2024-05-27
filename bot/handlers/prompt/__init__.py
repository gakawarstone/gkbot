from aiogram import Router

from . import gpt
from . import wait


def setup(r: Router):
    gpt.setup(r)
    wait.setup(r)
