from typing import Any

from extensions.handlers.message.base import BaseHandler
from extensions.handlers.message.send_voice import SendVoiceHandlerExtension

from ._states import FSM


class SendSpeechHandler(SendVoiceHandlerExtension, BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()

        await self.answer_text_as_voice(self.event.text)
