from typing import Any, AsyncGenerator
import time

from aiogram.types import Message
from aiogram.utils.formatting import BlockQuote

from services.llm import OpenRouter
from services.llm.openrouter import OpenRouterModel, StreamChunk
from extensions.handlers.message.markdown_render import MarkdownRenderHandlerExtension
from ._base import BaseHandler
from ._states import FSM


class AnswerHandler(MarkdownRenderHandlerExtension, BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        assert self.ctx.messages is not None

        if not self.event.text or self.event.text == "q":
            return

        self.ctx.messages.append(self.event.text)

        _message = await self.event.answer("Подождите")
        text = await self._stream_to_message(
            _message,
            OpenRouter(OpenRouterModel.SOLAR_PRO_3).stream(
                " | ".join(self.ctx.messages)
            ),
        )

        self.ctx.messages.append(text)
        await self.state.set_state(FSM.get_message)

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
