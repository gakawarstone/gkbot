from aiogram import Router

from . import menu
from . import add_book
from . import callbacks
from . import edit_book


def setup(r: Router):
    menu.setup(r)
    add_book.setup(r)
    callbacks.setup(r)
    edit_book.setup(r)
