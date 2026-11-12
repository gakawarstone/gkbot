import asyncio
import logging
import secrets
import time
from asyncio import Task
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

from aiogram import Bot
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.fsm.context import FSMContext
from aiogram.types import LinkPreviewOptions, Message, MessageGenerationStopped
from aiogram.utils.formatting import BlockQuote

from services.ai_response import split_response
from services.llm.openrouter import StreamChunk

logger = logging.getLogger(__name__)
DRAFT_MESSAGE_LIMIT = 4096

GenerationKey = tuple[int, int, int | None, int]


@dataclass
class ActiveGeneration:
    task: Task[str]
    state: FSMContext
    stopped: bool = False


# Stop updates have no from_user and therefore no injected FSMContext.
# Keep the source context and task until generation and cleanup have finished.
active_generations: dict[GenerationKey, ActiveGeneration] = {}


async def stop_generation(event: MessageGenerationStopped, bot: Bot) -> None:
    if event.chat.type != ChatType.PRIVATE:
        return
    key = (bot.id, event.chat.id, event.message_thread_id, event.draft_id)
    generation = active_generations.get(key)
    if generation and not generation.stopped and not generation.task.done():
        generation.stopped = True
        generation.task.cancel()


class AIChatStream:
    def __init__(
        self, event: Message, bot: Bot | None, state: FSMContext | None
    ) -> None:
        self.event = event
        self.bot = bot
        self.state = state

    async def _answer(self, text: str, **kwargs: Any) -> Message:
        request = self.event.answer(text, **kwargs)
        if self.event.message_thread_id is not None:
            request.message_thread_id = self.event.message_thread_id
        return await request

    async def _private_response(
        self, stream: AsyncGenerator[StreamChunk]
    ) -> str | None:
        assert self.bot is not None and self.state is not None
        draft_id = secrets.randbelow(2**31 - 1) + 1
        key = (
            self.bot.id,
            self.event.chat.id,
            self.event.message_thread_id,
            draft_id,
        )
        generation = ActiveGeneration(
            asyncio.create_task(self._stream_to_draft(stream, draft_id)), self.state
        )
        active_generations[key] = generation
        try:
            return await generation.task
        except asyncio.CancelledError:
            if not generation.stopped:
                raise
            await stream.aclose()
            await self._answer("Генерация остановлена.")
            return None
        finally:
            active_generations.pop(key, None)

    async def _send_draft(self, draft_id: int, text: str) -> bool:
        assert self.bot is not None
        try:
            await self.bot.send_message_draft(
                chat_id=self.event.chat.id,
                message_thread_id=self.event.message_thread_id,
                draft_id=draft_id,
                text=text,
                parse_mode="HTML",
                can_stop=True,
                keep_on_stop=False,
            )
        except TelegramAPIError as error:
            # Probe each generation: custom servers can be older than the client,
            # and transient draft failures must not disable drafts permanently.
            logger.warning("Draft streaming failed; using message fallback: %s", error)
            if isinstance(error, TelegramRetryAfter):
                await asyncio.sleep(error.retry_after)
            return False
        return True

    async def _stream_to_draft(
        self, stream: AsyncGenerator[StreamChunk], draft_id: int
    ) -> str:
        if not await self._send_draft(draft_id, "Подождите"):
            return await self._stream_to_message(
                await self._answer("Подождите"), stream
            )

        reason = ""
        text = ""
        last_update = time.monotonic()
        async for chunk, chunk_type in stream:
            if chunk_type == "reason":
                reason += chunk
            if chunk_type == "content":
                text += chunk
            now = time.monotonic()
            if now - last_update < 1.5:
                continue
            last_update = now
            chunks = split_response(text, DRAFT_MESSAGE_LIMIT)
            if not chunks and not reason:
                continue
            preview = chunks[-1] if chunks else BlockQuote(reason[-500:]).as_html()
            if not await self._send_draft(draft_id, preview):
                # Continue the same model stream with the content already read.
                return await self._stream_to_message(
                    await self._answer("Подождите"), stream, text=text, reason=reason
                )

        for chunk in split_response(text, DRAFT_MESSAGE_LIMIT) or [
            "Модель не вернула ответ."
        ]:
            await self._answer(
                chunk,
                parse_mode="HTML",
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )
        return text

    async def _stream_to_message(
        self,
        message: Message,
        stream: AsyncGenerator[StreamChunk],
        *,
        text: str = "",
        reason: str = "",
    ) -> str:
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
                request = messages[-1][0].answer(
                    chunk,
                    parse_mode="HTML",
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                )
                if self.event.message_thread_id is not None:
                    request.message_thread_id = self.event.message_thread_id
                message = await request
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
