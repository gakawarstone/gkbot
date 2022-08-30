from aiogram import Router

from . import menu


def setup(r: Router):
    menu.setup(r)
