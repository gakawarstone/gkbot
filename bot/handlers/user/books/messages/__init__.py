from ast import Add
from aiogram import Router

from . import add, show, edit_property


def setup(r: Router):
    add.setup(r)
    show.setup(r)
    edit_property.setup(r)
