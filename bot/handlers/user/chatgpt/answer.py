import base64
import time
from collections.abc import AsyncGenerator
from contextlib import aclosing
from typing import Any

from aiogram.enums import ChatType
from aiogram.types import Message

from extensions.handlers.message.file_extension import FileHandlerExtension
from extensions.handlers.message.markdown_render import MarkdownRenderHandlerExtension
from services.agents.image_explainer import ImageExplainer
from services.llm import OpenRouter
from services.llm.openrouter import DEFAULT_MODEL, StreamChunk
from ui.ai_chat_stream import AIChatStream

from ._base import BaseHandler
from ._states import FSM

__all__ = ("AnswerHandler", "time")


class AnswerHandler(BaseHandler, MarkdownRenderHandlerExtension, FileHandlerExtension):
    _MODEL = DEFAULT_MODEL

    async def handle(self) -> None:
        await self.state.set_state(FSM.finish)
        try:
            await self._answer_prompt()
        finally:
            # A concurrent /exit must not be undone by stream cleanup.
            if await self.state.get_state() == FSM.finish.state:
                await self.state.set_state(FSM.get_message)

    async def _answer_prompt(self) -> None:
        assert self.ctx.messages is not None

        delivery = self._delivery
        prompt = await self._build_prompt()
        if not prompt:
            await delivery._answer("Отправь текст или изображение с подписью.")
            return

        self.ctx.messages.append(prompt)

        async with aclosing(
            OpenRouter(self._MODEL).stream(
                " | ".join(self.ctx.messages), await self._get_images()
            )
        ) as stream:
            if self.event.chat.type == ChatType.PRIVATE:
                text = await delivery._private_response(stream)
            else:
                text = await delivery._stream_to_message(
                    await delivery._answer("Подождите"), stream
                )

        if text is not None:
            self.ctx.messages.append(text)

    async def _build_prompt(self) -> str | None:
        prompt = self.event.text or self.event.caption

        if not self.event.photo:
            return prompt

        if self._MODEL.supports_images:
            return prompt or "Проанализируй это изображение."

        image_description = await self._explain_image()
        if prompt:
            return f"{prompt}\n\nОписание изображения: {image_description}"
        return f"Проанализируй изображение по этому описанию: {image_description}"

    async def _get_images(self) -> list[str] | None:
        if not self.event.photo or not self._MODEL.supports_images:
            return None

        image_base64 = base64.b64encode((await self.photo_io).getvalue()).decode(
            "utf-8"
        )
        return [f"data:image/jpeg;base64,{image_base64}"]

    async def _explain_image(self) -> str:
        text = ""
        async for chunk in ImageExplainer.explain((await self.photo_io).getvalue()):
            text += chunk
        return text

    # Keep the existing entry points for callers while delivery lives in services.
    @property
    def _delivery(self) -> AIChatStream:
        return AIChatStream(self.event, self.data.get("bot"), self.data.get("state"))

    async def _answer(self, text: str, **kwargs: Any) -> Message:
        return await self._delivery._answer(text, **kwargs)

    async def _private_response(
        self, stream: AsyncGenerator[StreamChunk]
    ) -> str | None:
        return await self._delivery._private_response(stream)

    async def _send_draft(self, draft_id: int, text: str) -> bool:
        return await self._delivery._send_draft(draft_id, text)

    async def _stream_to_draft(
        self, stream: AsyncGenerator[StreamChunk], draft_id: int
    ) -> str:
        return await self._delivery._stream_to_draft(stream, draft_id)

    async def _stream_to_message(
        self,
        message: Message,
        stream: AsyncGenerator[StreamChunk],
        *,
        text: str = "",
        reason: str = "",
    ) -> str:
        return await self._delivery._stream_to_message(
            message, stream, text=text, reason=reason
        )

    async def _update_messages(
        self, messages: list[tuple[Message, str]], chunks: list[str]
    ) -> None:
        await self._delivery._update_messages(messages, chunks)
