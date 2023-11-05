from typing import Any

from extensions.handlers.message.base import BaseHandler
from extensions.handlers.message.send_voice import SendVoiceHandlerExtention
from services.text_to_speach import TextToSpeachService
from ._states import FSM


class SendSpeachHandler(SendVoiceHandlerExtention, BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()
        voice_file = await TextToSpeachService.convert_text_to_speach(self.event.text)
        await self.answer_voice(voice_file)
