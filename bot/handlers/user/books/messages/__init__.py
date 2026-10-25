from aiogram import Router

from . import add, edit_property, show


def setup(r: Router):
    add.setup(r)
    show.setup(r)
    edit_property.setup(r)
