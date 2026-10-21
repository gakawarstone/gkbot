from aiogram import Router

from . import wait
from . import generate_image


def setup(r: Router):
    wait.setup(r)
    generate_image.setup(r)
