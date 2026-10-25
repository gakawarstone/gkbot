import base64
import time
from collections.abc import AsyncGenerator

from aiogram.types import LinkPreviewOptions, Message
from aiogram.utils.formatting import BlockQuote

from extensions.handlers.message.file_extension import FileHandlerExtension
from extensions.handlers.message.markdown_render import MarkdownRenderHandlerExtension
from services.agents.image_explainer import ImageExplainer
from services.llm import OpenRouter
from services.llm.openrouter import DEFAULT_MODEL, StreamChunk

from ._base import BaseHandler
from ._response import split_response
from ._states import FSM


class AnswerHandler(BaseHandler, MarkdownRenderHandlerExtension, FileHandlerExtension):
    _MODEL = DEFAULT_MODEL

    async def handle(self) -> None:
        await self.state.set_state(FSM.finish)
        try:
            await self._answer_prompt()
        finally:
            await self.state.set_state(FSM.get_message)

    async def _answer_prompt(self) -> None:
        assert self.ctx.messages is not None

        prompt = await self._build_prompt()
        if not prompt:
            await self.event.answer("Отправь текст или изображение с подписью.")
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
        self, message: Message, stream: AsyncGenerator[StreamChunk]
    ) -> str:
        reason = ""
        text = ""
        messages = [(message, message.html_text or "")]
        last_update = time.monotonic()

        async for chunk, chunk_type in stream:
            if chunk_type == "reason":
                reason += chunk
            if chunk_type == "content":
                text += chunk

            now = time.monotonic()
            if now - last_update >= 1.5:
                last_update = now
                if not text and reason:
                    chunks = [BlockQuote(reason[-500:]).as_html()]
                else:
                    chunks = split_response(text)
                await self._update_messages(messages, chunks)

        await self._update_messages(
            messages, split_response(text) or ["Модель не вернула ответ."]
        )
        return text

    async def _update_messages(
        self, messages: list[tuple[Message, str]], chunks: list[str]
    ) -> None:
        for index, chunk in enumerate(chunks):
            if index >= len(messages):
                message = await messages[-1][0].answer(
                    chunk,
                    parse_mode="HTML",
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                )
            else:
                message, previous_text = messages[index]
                if chunk != previous_text:
                    await message.edit_text(
                        chunk,
                        parse_mode="HTML",
                        link_preview_options=LinkPreviewOptions(is_disabled=True),
                    )
            if index >= len(messages):
                messages.append((message, chunk))
            else:
                messages[index] = (message, chunk)

        # Completing Markdown can remove delimiters and reduce the chunk count.
        while len(messages) > max(1, len(chunks)):
            await messages[-1][0].delete()
            messages.pop()
