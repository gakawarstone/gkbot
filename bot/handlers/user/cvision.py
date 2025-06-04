from typing import Any
import base64
import time

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.state import State, StateFilter, StatesGroup

from services.llm import OpenRouter
from extensions.handlers.message.base import BaseHandler
from extensions.handlers.message.file_extension import FileHandlerExtension
from ._commands import USER_COMMANDS


class _CVisionFSM(StatesGroup):
    finish = State()
    get_response = State()


FSM = _CVisionFSM


class StartChatHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.get_response)
        await self.event.delete()
        await self.event.answer("Задайте свой вопрос 🤔")


class AnswerHandler(FileHandlerExtension):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()

        image_bytes = (await self.photo_io).getvalue()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        image_data_url = f"data:image/jpeg;base64,{image_base64}"

        _message = await self.event.answer("Подождите..")

        text = ""
        last_update = time.time()
        async for ch in OpenRouter.stream("What is on this image?", [image_data_url]):
            text += ch
            now = time.time()
            if now - last_update >= 0.5:
                await _message.edit_text(text)
                last_update = now
        await _message.edit_text(text)


def setup(r: Router):
    r.message.register(StartChatHandler, Command(commands=USER_COMMANDS.cvision))
    r.message.register(AnswerHandler, StateFilter(FSM.get_response))
