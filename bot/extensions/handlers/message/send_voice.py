from abc import ABC

from aiogram.types import BufferedInputFile

from services.ffmpeg import FfmpegService
from services.tts import TextToSpeechService, TTSProviderType

from .base import BaseHandler as _BaseHandler


class SendVoiceHandlerExtension(_BaseHandler, ABC):
    async def answer_text_as_voice(self, text: str | None) -> None:
        if not text:
            raise ValueError("TTS requires non-empty text")

        voice_file = await TextToSpeechService.convert_text_to_speech(
            text, provider=TTSProviderType.EDGE
        )
        await self.answer_voice(voice_file)

    async def answer_voice(self, music: bytes) -> None:
        voice_file = await FfmpegService.convert_music_to_voice(music)
        await self.event.answer_voice(BufferedInputFile(voice_file, "voice.ogg"))
