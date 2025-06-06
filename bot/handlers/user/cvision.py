from typing import Any
import time
import re

from aiogram import Router
from aiogram.utils.formatting import Bold
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.state import State, StatesGroup

from services.agents.image_explainer import ImageExplainer
from extensions.handlers.message.one_time_extension import (
    OneTimeMessageHandlerExtension,
)
from extensions.handlers.message.file_extension import FileHandlerExtension
from ._commands import USER_COMMANDS


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


class AnswerHandler(FileHandlerExtension):
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
                await _message.edit_text(text)
                last_update = now
        await _message.edit_text(self._render(text))

    @staticmethod
    def _render(markdown_string: str) -> str:
        bold_pattern = r"\*\*([^*]+)\*\*"

        def replace_bold_func(match):
            text = match.group(1)
            return Bold(text).as_html()

        result = re.sub(bold_pattern, replace_bold_func, markdown_string)

        return result


def setup(r: Router):
    r.message.register(StartChatHandler, Command(commands=USER_COMMANDS.cvision))
    r.message.register(AnswerHandler, StateFilter(FSM.get_response))
