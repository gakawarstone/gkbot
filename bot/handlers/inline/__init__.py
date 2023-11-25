from aiogram import Router

from . import tiktok, youtube, chance, choose_list


def setup(r: Router):
    tiktok.setup(r)
    youtube.setup(r)
    chance.setup(r)
    choose_list.setup(r)
