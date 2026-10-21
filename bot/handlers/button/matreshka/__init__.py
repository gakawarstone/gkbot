from aiogram import Router

from . import download


def setup(router: Router) -> None:
    download.setup(router)
