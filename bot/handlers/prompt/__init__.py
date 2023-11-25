from aiogram import Router

from . import gpt


def setup(r: Router):
    gpt.setup(r)
