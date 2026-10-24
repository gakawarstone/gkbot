import asyncio
import xml.etree.ElementTree as ET
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from itertools import count
from typing import Any
from unittest.mock import patch

import pytest
from aiogram import Bot, Dispatcher, Router
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramNetworkError,
    TelegramNotFound,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import (
    EditMessageText,
    SendMessage,
    SendMessageDraft,
    TelegramMethod,
)
from aiogram.types import Chat, Message, MessageGenerationStopped, Update
from aiogram.utils.formatting import sizeof

from handlers.user import chatgpt
from handlers.user.chatgpt._generation import stop_generation
from handlers.user.chatgpt._states import FSM
from handlers.user.chatgpt.answer import AnswerHandler
from services.llm.openrouter import StreamChunk


def visible_text(html: str) -> str:
    return "".join(ET.fromstring(f"<root>{html}</root>").itertext())


class RecordingSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.requests: list[TelegramMethod[Any]] = []
        self.messages: dict[int, Message] = {}
        self.failures: dict[
            type[TelegramMethod[Any]], list[TelegramAPIError | None]
        ] = {}

    async def close(self) -> None:
        pass

    async def stream_content(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes]:
        yield b""

    async def make_request(
        self, bot: Bot, method: TelegramMethod[Any], timeout: int | None = None
    ) -> Any:
        self.requests.append(method)
        if (failures := self.failures.get(type(method))) and (error := failures.pop(0)):
            raise error
        if isinstance(method, SendMessage):
            message = Message(
                message_id=len(self.messages) + 1,
                date=datetime.now(UTC),
                chat=Chat(id=int(method.chat_id), type="private"),
                message_thread_id=method.message_thread_id,
                text=method.text,
            ).as_(bot)
            self.messages[message.message_id] = message
            return message
        if isinstance(method, EditMessageText):
            assert method.message_id is not None
            self.messages[method.message_id] = self.messages[
                method.message_id
            ].model_copy(update={"text": method.text})
            return self.messages[method.message_id]
        return True


def make_handler(
    chat_type: str = "private", thread_id: int | None = None
) -> tuple[AnswerHandler, RecordingSession, FSMContext, list[str]]:
    session = RecordingSession()
    bot = Bot("123456:TEST", session=session)
    event = Message(
        message_id=100,
        date=datetime.now(UTC),
        chat=Chat(id=123, type=chat_type),
        message_thread_id=thread_id,
        # Explicitly exercise thread IDs even without is_topic_message=True.
        is_topic_message=False,
        text="prompt",
    ).as_(bot)
    state = FSMContext(
        MemoryStorage(),
        StorageKey(bot_id=bot.id, chat_id=123, user_id=123, thread_id=thread_id),
    )
    history: list[str] = []
    handler = AnswerHandler(event, bot=bot, state=state, data={"messages": history})
    return handler, session, state, history


async def chunks_stream(text: str) -> AsyncGenerator[StreamChunk]:
    for index in range(0, len(text), 701):
        yield StreamChunk(text[index : index + 701], "content")


@pytest.mark.parametrize(
    ("text", "thread_id", "expected"),
    [
        ("**hello <&>**" * 100, None, "hello <&>" * 100),
        ("😀" * 6000, 42, "😀" * 6000),
    ],
)
async def test_private_drafts_finalize_complete_bounded_response(
    text: str, thread_id: int | None, expected: str
) -> None:
    handler, session, state, history = make_handler(thread_id=thread_id)
    ticks = count(step=2)
    with (
        patch(
            "handlers.user.chatgpt.answer.OpenRouter.stream",
            return_value=chunks_stream(text),
        ),
        patch(
            "handlers.user.chatgpt.answer.time",
            monotonic=lambda: next(ticks),
        ),
    ):
        await handler.handle()

    drafts = [r for r in session.requests if isinstance(r, SendMessageDraft)]
    final = [r for r in session.requests if isinstance(r, SendMessage)]
    assert len(drafts) > 1
    assert len({r.draft_id for r in drafts}) == 1
    assert drafts[0].draft_id != 0
    assert all(r.can_stop is True for r in drafts)
    assert all(r.message_thread_id == thread_id for r in drafts + final)
    assert all(r.chat_id == 123 for r in drafts + final)
    assert all(0 < sizeof(visible_text(r.text or "")) <= 4096 for r in drafts + final)
    assert "".join(visible_text(r.text) for r in final) == expected
    if sizeof(expected) <= 4096:
        assert len(final) == 1
    assert history == ["prompt", text]
    assert await state.get_state() == FSM.get_message.state


async def test_group_fallback_preserves_topic_and_complete_response() -> None:
    handler, session, state, history = make_handler("supergroup", thread_id=42)
    text = "a" * 3500
    with patch(
        "handlers.user.chatgpt.answer.OpenRouter.stream",
        return_value=chunks_stream(text),
    ):
        await handler.handle()
    assert not any(isinstance(r, SendMessageDraft) for r in session.requests)
    assert all(
        r.message_thread_id == 42
        for r in session.requests
        if isinstance(r, SendMessage)
    )
    assert (
        "".join(visible_text(m.text or "") for m in session.messages.values()) == text
    )
    assert history == ["prompt", text]
    assert await state.get_state() == FSM.get_message.state


@pytest.mark.parametrize(
    ("fail_at", "error_type"),
    [(1, TelegramNotFound), (3, TelegramNetworkError)],
)
async def test_draft_failure_preserves_complete_response(
    fail_at: int, error_type: type[TelegramAPIError]
) -> None:
    handler, session, state, history = make_handler(thread_id=42)
    method: TelegramMethod[Any] = SendMessageDraft(chat_id=123, draft_id=1)
    session.failures[SendMessageDraft] = [None] * (fail_at - 1) + [
        error_type(method=method, message="draft unavailable")
    ]
    text = "before\n\n" + "😀<&>" * 1200
    closed = asyncio.Event()

    async def stream(*args: Any) -> AsyncGenerator[StreamChunk]:
        try:
            async for chunk in chunks_stream(text):
                yield chunk
        finally:
            closed.set()

    ticks = count(step=2)
    with (
        patch("handlers.user.chatgpt.answer.OpenRouter.stream", side_effect=stream),
        patch(
            "handlers.user.chatgpt.answer.time",
            monotonic=lambda: next(ticks),
        ),
    ):
        await handler.handle()
    assert closed.is_set()
    assert (
        "".join(visible_text(m.text or "") for m in session.messages.values()) == text
    )
    assert all(
        r.message_thread_id == 42
        for r in session.requests
        if isinstance(r, SendMessage)
    )
    assert history == ["prompt", text]
    assert await state.get_state() == FSM.get_message.state


@pytest.mark.parametrize("failure", ["model", "final_message"])
async def test_failure_closes_stream_and_recovers_state(failure: str) -> None:
    handler, session, state, history = make_handler()
    closed = asyncio.Event()
    if failure == "final_message":
        session.failures[SendMessage] = [
            TelegramBadRequest(
                method=SendMessage(chat_id=123, text="answer"), message="send failed"
            )
        ]

    async def stream(*args: Any) -> AsyncGenerator[StreamChunk]:
        try:
            yield StreamChunk("answer", "content")
            if failure == "model":
                raise ConnectionError("model failed")
        finally:
            closed.set()

    with (
        patch("handlers.user.chatgpt.answer.OpenRouter.stream", side_effect=stream),
        patch("handlers.user.chatgpt.answer.time", monotonic=lambda: 0),
        pytest.raises(ConnectionError if failure == "model" else TelegramBadRequest),
    ):
        await handler.handle()
    assert closed.is_set()
    assert history == ["prompt"]
    assert await state.get_state() == FSM.get_message.state


@pytest.mark.parametrize("exit_before_stop", [False, True])
async def test_native_stop_cancels_only_matching_generation_and_preserves_exit(
    exit_before_stop: bool,
) -> None:
    handler, session, state, history = make_handler(thread_id=42)
    started = asyncio.Event()
    closed = asyncio.Event()

    async def stream(*args: Any) -> AsyncGenerator[StreamChunk]:
        try:
            yield StreamChunk("partial", "content")
            started.set()
            await asyncio.Future()
        finally:
            closed.set()

    router = Router()
    chatgpt.setup(router)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    with patch("handlers.user.chatgpt.answer.OpenRouter.stream", side_effect=stream):
        task = asyncio.create_task(handler.handle())
        await asyncio.wait_for(started.wait(), 1)
        draft = next(r for r in session.requests if isinstance(r, SendMessageDraft))
        event = MessageGenerationStopped(
            chat=handler.event.chat, draft_id=draft.draft_id, message_thread_id=42
        )
        if exit_before_stop:
            await state.clear()
        # Unknown/stale drafts, topics and bot instances must not cancel this task.
        for update in [
            event.model_copy(update={"draft_id": draft.draft_id + 1}),
            event.model_copy(update={"message_thread_id": 43}),
        ]:
            await stop_generation(update, handler.bot)
        await stop_generation(event, Bot("654321:TEST"))
        await asyncio.sleep(0)
        assert not closed.is_set()
        # Real aiogram routing, no from_user or FSMContext on the update.
        await dispatcher.feed_update(
            handler.bot, Update(update_id=1, stopped_message_generation=event)
        )
        await stop_generation(event, handler.bot)  # duplicate stop is harmless
        await asyncio.wait_for(task, 1)
        await stop_generation(event, handler.bot)  # stale stop is harmless
    assert closed.is_set()
    assert history == ["prompt"]
    assert await state.get_state() == (
        None if exit_before_stop else FSM.get_message.state
    )
    final = [r for r in session.requests if isinstance(r, SendMessage)]
    assert len(final) == 1
    assert final[0].text
    assert final[0].message_thread_id == 42
    await dispatcher.storage.close()


async def test_external_cancellation_propagates_and_closes_stream() -> None:
    handler, _session, state, history = make_handler()
    started = asyncio.Event()
    closed = asyncio.Event()

    async def stream(*args: Any) -> AsyncGenerator[StreamChunk]:
        try:
            started.set()
            await asyncio.Future()
            yield StreamChunk("unused", "content")
        finally:
            closed.set()

    with patch("handlers.user.chatgpt.answer.OpenRouter.stream", side_effect=stream):
        task = asyncio.create_task(handler.handle())
        await asyncio.wait_for(started.wait(), 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    assert closed.is_set()
    assert history == ["prompt"]
    assert await state.get_state() == FSM.get_message.state


async def test_reason_only_response_finishes_with_nonempty_status() -> None:
    handler, session, state, _history = make_handler()
    reason = "thinking <&>"

    async def stream(*args: Any) -> AsyncGenerator[StreamChunk]:
        yield StreamChunk(reason, "reason")

    with patch("handlers.user.chatgpt.answer.OpenRouter.stream", side_effect=stream):
        await handler.handle()
    final = [r for r in session.requests if isinstance(r, SendMessage)]
    assert len(final) == 1
    assert visible_text(final[0].text)
    assert visible_text(final[0].text) != reason
    assert await state.get_state() == FSM.get_message.state


@pytest.mark.parametrize("status_fails", [False, True])
async def test_stop_while_sending_draft_closes_suspended_stream(
    status_fails: bool,
) -> None:
    handler, session, state, history = make_handler(thread_id=42)
    sending = asyncio.Event()
    closed = asyncio.Event()

    async def stream(*args: Any) -> AsyncGenerator[StreamChunk]:
        try:
            yield StreamChunk("partial", "content")
            pytest.fail("The cancelled model stream must not be read again")
        finally:
            closed.set()

    send_draft = handler.bot.send_message_draft

    async def blocking_draft(**kwargs: Any) -> bool:
        if not session.requests:
            return await send_draft(**kwargs)
        sending.set()
        await asyncio.Future()
        return True

    if status_fails:
        session.failures[SendMessage] = [
            TelegramBadRequest(
                method=SendMessage(chat_id=123, text="status"), message="status failed"
            )
        ]
    ticks = count(step=2)
    with (
        patch("handlers.user.chatgpt.answer.OpenRouter.stream", side_effect=stream),
        patch.object(handler.bot, "send_message_draft", side_effect=blocking_draft),
        patch(
            "handlers.user.chatgpt.answer.time",
            monotonic=lambda: next(ticks),
        ),
    ):
        task = asyncio.create_task(handler.handle())
        await asyncio.wait_for(sending.wait(), 1)
        draft = next(r for r in session.requests if isinstance(r, SendMessageDraft))
        await stop_generation(
            MessageGenerationStopped(
                chat=handler.event.chat, draft_id=draft.draft_id, message_thread_id=42
            ),
            handler.bot,
        )
        if status_fails:
            with pytest.raises(TelegramBadRequest, match="status failed"):
                await task
        else:
            await task
    assert closed.is_set()
    assert history == ["prompt"]
    assert await state.get_state() == FSM.get_message.state
