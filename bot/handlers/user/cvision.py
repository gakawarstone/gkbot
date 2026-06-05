from typing import Any
import time

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.state import State, StatesGroup

from services.agents.image_explainer import ImageExplainer
from extensions.handlers.message.markdown_render import MarkdownRenderHandlerExtension
from extensions.handlers.message.one_time_extension import (
    OneTimeMessageHandlerExtension,
)
from extensions.handlers.message.file_extension import FileHandlerExtension
from configs.commands import USER_COMMANDS


class _CVisionFSM(StatesGroup):
    finish = State()
    get_response = State()


FSM = _CVisionFSM


class StartChatHandler(OneTimeMessageHandlerExtension):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.get_response)
        await self.event.delete()
        self._set_one_time_message(
            await self.event.answer("Пришлите изображение для описания")
        )


class AnswerHandler(MarkdownRenderHandlerExtension, FileHandlerExtension):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()

        image_bytes = (await self.photo_io).getvalue()

        _message = await self.event.answer("Подождите..")
        text = ""
        last_update = time.time()
        async for chunk in ImageExplainer.explain(image_bytes):
            text += chunk
            now = time.time()
            if now - last_update >= 0.5:
                await _message.edit_text(
                    text.replace("<", "__tagopen__").replace(">", "__tagclose__")
                )
                last_update = now
        await _message.edit_text(self._render_markdown(text))


def setup(r: Router):
    r.message.register(StartChatHandler, Command(commands=USER_COMMANDS.cvision))
    r.message.register(AnswerHandler, StateFilter(FSM.get_response))
