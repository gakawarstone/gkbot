from typing import Any, AsyncGenerator
import base64
import time

from aiogram.types import Message
from aiogram.utils.formatting import BlockQuote

from services.agents.image_explainer import ImageExplainer
from services.llm import OpenRouter
from services.llm.openrouter import OpenRouterModel, StreamChunk
from extensions.handlers.message.file_extension import FileHandlerExtension
from extensions.handlers.message.markdown_render import MarkdownRenderHandlerExtension
from ._base import BaseHandler
from ._states import FSM


class AnswerHandler(BaseHandler, MarkdownRenderHandlerExtension, FileHandlerExtension):
    _MODEL = OpenRouterModel.QWEN_36_PLUS

    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        assert self.ctx.messages is not None

        prompt = await self._build_prompt()
        if not prompt or prompt == "q":
            await self.event.answer("Пока")
            return

        self.ctx.messages.append(prompt)

        _message = await self.event.answer("Подождите")
        text = await self._stream_to_message(
            _message,
            OpenRouter(self._MODEL).stream(
                " | ".join(self.ctx.messages), await self._get_images()
            ),
        )

        self.ctx.messages.append(text)
        await self.state.set_state(FSM.get_message)

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

    async def _stream_to_message(
        self, message: Message, stream: AsyncGenerator[StreamChunk, None]
    ) -> str:
        reason = ""
        text = ""
        full_text = ""
        last_update = time.time()

        async for chunk, chunk_type in stream:
            if chunk_type == "reason":
                reason += chunk
            if chunk_type == "content":
                text += chunk

            now = time.time()
            if now - last_update >= 1.5:
                last_update = now
                _message_text = ""

                if not text and reason:
                    _message_text += BlockQuote(reason[-500:]).as_html()
                else:
                    _message_text += text.replace("<", "__tagopen__").replace(
                        ">", "__tagclose__"
                    )

                if len(_message_text) > 1500:
                    text_chunks = text.split("\n\n")
                    await message.edit_text(
                        self._render_markdown("\n\n".join(text_chunks[:-1]))
                    )
                    full_text += "\n\n".join(text_chunks[:-1])
                    text = text_chunks[-1]
                    message = await message.answer(text)
                    continue

                await message.edit_text(_message_text, disable_web_page_preview=True)

        full_text += text
        await message.edit_text(self._render_markdown(text))
        return full_text
