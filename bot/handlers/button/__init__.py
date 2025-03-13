from aiogram import Router

from . import youtube_audio_download


def setup(r: Router):
    youtube_audio_download.setup(r)
