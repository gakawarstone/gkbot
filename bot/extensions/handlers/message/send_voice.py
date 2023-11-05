from abc import ABC

from aiogram.types import BufferedInputFile

from services.ffmpeg import FfmpegService
from .base import BaseHandler as _BaseHandler


class SendVoiceHandlerExtention(_BaseHandler, ABC):
    async def answer_voice(self, music: bytes) -> None:
        voice_file = await FfmpegService.convert_music_to_voice(music)
        await self.event.answer_voice(BufferedInputFile(voice_file, "voice.ogg"))
