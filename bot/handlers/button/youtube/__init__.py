from aiogram import Router

from . import download_audio
from . import download_video


def setup(r: Router):
    download_audio.setup(r)
    download_video.setup(r)
