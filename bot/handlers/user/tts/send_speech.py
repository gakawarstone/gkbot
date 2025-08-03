from typing import Any

from extensions.handlers.message.base import BaseHandler
from extensions.handlers.message.send_voice import SendVoiceHandlerExtension
from services.text_to_speech import TextToSpeechService
from ._states import FSM


class SendSpeechHandler(SendVoiceHandlerExtension, BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()

        if self.event.text is None:
            raise ValueError("event.text is None")

        voice_file = await TextToSpeechService.convert_text_to_speech(self.event.text)
        await self.answer_voice(voice_file)
