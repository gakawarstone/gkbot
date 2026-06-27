from aiogram import Router

from . import download


def setup(r: Router):
    download.setup(r)
