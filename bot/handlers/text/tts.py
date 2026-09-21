from typing import Any

from aiogram import Router
from aiogram.filters import and_f

from extensions.handlers.message.base import BaseHandler
from extensions.handlers.message.send_voice import SendVoiceHandlerExtension
from filters.chat_type import ChatType, ChatTypeFilter
from filters.long_message import LongMessageFilter


class TextToSpeechHandler(SendVoiceHandlerExtension, BaseHandler):
    async def handle(self) -> Any:
        await self.event.delete()

        await self.answer_text_as_voice(self.event.text)


def setup(r: Router):
    r.message.register(
        TextToSpeechHandler,
        and_f(LongMessageFilter(), ChatTypeFilter(ChatType.private)),
    )
