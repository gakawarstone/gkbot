from aiogram import Router

from . import tiktok, youtube, chance, choose_list, joke


def setup(r: Router):
    tiktok.setup(r)
    youtube.setup(r)
    chance.setup(r)
    choose_list.setup(r)
    joke.setup(r)
