from aiogram import Router

from . import delete_message, matreshka, pornhub, porno365, sasflix, vk, youtube


def setup(r: Router):
    youtube.setup(r)
    delete_message.setup(r)
    matreshka.setup(r)
    vk.setup(r)
    pornhub.setup(r)
    porno365.setup(r)
    sasflix.setup(r)
