import time
from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from configs.commands import USER_COMMANDS
from extensions.handlers.message.file_extension import FileHandlerExtension
from extensions.handlers.message.markdown_render import MarkdownRenderHandlerExtension
from extensions.handlers.message.one_time_extension import (
    OneTimeMessageHandlerExtension,
)
from services.agents.image_explainer import ImageExplainer
from utils.status_message import temporary_status


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

        async with temporary_status(self.event, "Подождите..") as status:
            response: Message | None = None
            text = ""
            last_update = time.time()
            async for chunk in ImageExplainer.explain(image_bytes):
                text += chunk
                now = time.time()
                if text and now - last_update >= 0.5:
                    preview = text.replace("<", "__tagopen__").replace(
                        ">", "__tagclose__"
                    )
                    if response is None:
                        response = await status.publish(preview)
                    else:
                        await response.edit_text(preview)
                    last_update = now
            result = (
                self._render_markdown(text) if text else "Не удалось получить ответ."
            )
            if response is None:
                await status.publish(result)
            else:
                await response.edit_text(result)


def setup(r: Router) -> None:
    r.message.register(StartChatHandler, Command(commands=USER_COMMANDS.cvision))
    r.message.register(AnswerHandler, StateFilter(FSM.get_response))
