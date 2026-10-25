from aiogram import Router

from . import instagram, jutsu, tiktok, tts, vk, ytdlp, ytdlp_short


def setup(r: Router):
    tiktok.setup(r)
    ytdlp.setup(r)
    jutsu.setup(r)
    ytdlp_short.setup(r)
    instagram.setup(r)
    tts.setup(r)
    vk.setup(r)
