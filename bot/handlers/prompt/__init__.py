from aiogram import Router

from . import gpt
from . import wait
from . import generate_image


def setup(r: Router):
    gpt.setup(r)
    wait.setup(r)
    generate_image.setup(r)
