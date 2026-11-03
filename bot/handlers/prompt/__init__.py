from aiogram import Router

from . import generate_image, wait


def setup(r: Router):
    wait.setup(r)
    generate_image.setup(r)
