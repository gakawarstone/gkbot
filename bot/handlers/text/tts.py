from typing import Any

from aiogram import Router
from aiogram.filters import and_f

from extensions.handlers.message.base import BaseHandler
from extensions.handlers.message.send_voice import SendVoiceHandlerExtension
from filters.long_message import LongMessageFilter
from filters.chat_type import ChatTypeFilter, ChatType
from services.tts import TextToSpeechService, TTSProviderType


class TextToSpeechHandler(SendVoiceHandlerExtension, BaseHandler):
    async def handle(self) -> Any:
        await self.event.delete()

        if not self.event.text:
            raise ValueError("TTS requires non-empty text")

        voice_file = await TextToSpeechService.convert_text_to_speech(
            self.event.text, provider=TTSProviderType.EDGE
        )
        await self.answer_voice(voice_file)


def setup(r: Router):
    r.message.register(
        TextToSpeechHandler,
        and_f(LongMessageFilter(), ChatTypeFilter(ChatType.private)),
    )
