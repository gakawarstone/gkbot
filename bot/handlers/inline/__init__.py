from aiogram import Router

from . import chance, choose_list, joke, tiktok, youtube


def setup(r: Router):
    tiktok.setup(r)
    youtube.setup(r)
    chance.setup(r)
    choose_list.setup(r)
    joke.setup(r)
