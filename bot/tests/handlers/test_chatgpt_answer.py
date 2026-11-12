import xml.etree.ElementTree as ET
from asyncio import CancelledError
from collections.abc import AsyncGenerator
from itertools import count
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import EditMessageText
from aiogram.types import Message
from aiogram.utils.formatting import sizeof

from extensions.handlers.message.markdown_render import parse_markdown
from handlers.user.chatgpt._response import (
    RESPONSE_MESSAGE_LIMIT,
    split_response,
    split_text,
)
from handlers.user.chatgpt._states import FSM
from handlers.user.chatgpt.answer import AnswerHandler
from services.llm.openrouter import StreamChunk


def visible_text(html: str) -> str:
    root = ET.fromstring(f"<root>{html}</root>")
    assert all(
        node.tag in {"root", "b", "code", "pre", "blockquote"} for node in root.iter()
    )
    return "".join(root.itertext())


@pytest.mark.parametrize(
    "text",
    [
        "",
        "a" * 1499,
        "a" * 1500,
        "a" * 1501,
        "a" * 6000,
        "длинный абзац " * 600,
        "first\n\n" + "second line\n" * 500,
        "😀<&>" * 1000,
        "\n" * 3001,
    ],
    ids=[
        "empty",
        "under-limit",
        "exact-limit",
        "over-limit",
        "word",
        "paragraph",
        "lines",
        "unicode",
        "newlines",
    ],
)
def test_split_text_preserves_every_character(text: str) -> None:
    chunks = split_text(text)
    assert "".join(chunks) == text
    assert all(0 < sizeof(chunk) <= RESPONSE_MESSAGE_LIMIT for chunk in chunks)


@pytest.mark.parametrize(
    ("text", "limit", "expected"),
    [
        ("1234\n\n5678\n90", 11, ["1234\n\n", "5678\n90"]),
        ("1234\n567 890", 9, ["1234\n", "567 890"]),
        ("1234 567890", 8, ["1234 ", "567890"]),
        ("1234567890", 5, ["12345", "67890"]),
        ("😀😀😀", 3, ["😀", "😀", "😀"]),
    ],
)
def test_split_text_prefers_boundaries(
    text: str, limit: int, expected: list[str]
) -> None:
    assert split_text(text, limit) == expected


@pytest.mark.parametrize("limit", [-1, 0, 1])
def test_split_text_rejects_invalid_limit(limit: int) -> None:
    with pytest.raises(ValueError, match="limit"):
        split_text("text", limit)


@pytest.mark.parametrize(
    ("markdown", "tag"),
    [
        ("**" + "bold 😀 <&> " * 1000 + "**", "b"),
        ("`" + "inline 😀 <&> " * 1000 + "`", "code"),
        ("```python\n" + "print('<&>😀')\n" * 1000 + "```", "pre"),
        ("```\n" + "a" * 6000 + "\n```", "pre"),
    ],
    ids=["bold", "inline", "python", "unlabelled"],
)
def test_split_response_preserves_formatting(markdown: str, tag: str) -> None:
    chunks = split_response(markdown)
    assert len(chunks) > 1
    assert "".join(map(visible_text, chunks)) == parse_markdown(markdown).render()[0]
    for chunk in chunks:
        assert 0 < sizeof(visible_text(chunk)) <= RESPONSE_MESSAGE_LIMIT
        assert ET.fromstring(f"<root>{chunk}</root>").find(tag) is not None
        if "```python" in markdown:
            assert 'class="language-python"' in chunk


@pytest.mark.parametrize(
    ("markdown", "expected"),
    [
        ("<b>literal</b> & &#42;", "<b>literal</b> & &#42;"),
        ("**<b>bold & 😀</b>**", "<b>bold & 😀</b>"),
        ("`**not bold** * <&>`", "**not bold** * <&>"),
        ("```python\n**not bold** * <&>\n```", "**not bold** * <&>\n"),
        ("```\n  indented\n\n```", "  indented\n\n"),
        ("```code without a newline```", "code without a newline"),
        ("unfinished **bold <&>", "unfinished **bold <&>"),
        ("unfinished ```python\n<&>", "unfinished ```python\n<&>"),
        ("list\n* first * second", "list\n📌 first👉 second"),
    ],
)
def test_markdown_is_escaped_once(markdown: str, expected: str) -> None:
    assert "".join(map(visible_text, split_response(markdown))) == expected


class MessageRecorder:
    def __init__(self) -> None:
        self.messages: list[MagicMock] = []
        self.emissions: list[str] = []

    def make_message(self, text: str = "Подождите") -> MagicMock:
        message = MagicMock(spec=Message)
        message.html_text = text

        async def edit(text: str, **kwargs: Any) -> None:
            self.emissions.append(text)
            message.html_text = text

        async def answer(text: str, **kwargs: Any) -> MagicMock:
            self.emissions.append(text)
            return self.make_message(text)

        async def delete() -> None:
            self.messages.remove(message)

        message.edit_text = AsyncMock(side_effect=edit)
        message.answer = AsyncMock(side_effect=answer)
        message.delete = AsyncMock(side_effect=delete)
        self.messages.append(message)
        return message


async def response_stream(chunks: list[StreamChunk]) -> AsyncGenerator[StreamChunk]:
    for chunk in chunks:
        yield chunk


@pytest.mark.parametrize("live_updates", [False, True])
@pytest.mark.parametrize(
    "text",
    [
        "a" * 1500,
        "a" * 1501,
        "long paragraph " * 1000,
        "before\n\n```python\n" + "print('<&>😀')\n" * 500 + "```\n\nafter",
        "**" + "😀" * 2000 + "**",
    ],
    ids=["exact-limit", "over-limit", "paragraph", "code", "unicode-bold"],
)
async def test_stream_sends_bounded_html_and_returns_original_response(
    text: str, live_updates: bool
) -> None:
    recorder = MessageRecorder()
    message = recorder.make_message()
    handler = AnswerHandler(event=message)
    chunks = [
        StreamChunk(text[i : i + 701], "content") for i in range(0, len(text), 701)
    ]
    ticks = count(step=2 if live_updates else 0)
    with patch(
        "handlers.user.chatgpt.answer.time.monotonic", side_effect=lambda: next(ticks)
    ):
        result = await handler._stream_to_message(message, response_stream(chunks))

    assert result == text
    assert (
        "".join(visible_text(msg.html_text) for msg in recorder.messages)
        == parse_markdown(text).render()[0]
    )
    assert recorder.emissions
    assert all(
        0 < sizeof(visible_text(chunk)) <= RESPONSE_MESSAGE_LIMIT
        for chunk in recorder.emissions
    )


async def test_completing_markdown_removes_surplus_preview_messages() -> None:
    recorder = MessageRecorder()
    message = recorder.make_message()
    handler = AnswerHandler(event=message)
    ticks = count(step=2)
    text = "**" + "a" * 1499
    with patch(
        "handlers.user.chatgpt.answer.time.monotonic", side_effect=lambda: next(ticks)
    ):
        result = await handler._stream_to_message(
            message,
            response_stream(
                [StreamChunk(text, "content"), StreamChunk("**", "content")]
            ),
        )
    assert result == text + "**"
    assert len(recorder.messages) == 1
    assert message.html_text == "<b>" + "a" * 1499 + "</b>"


@pytest.mark.parametrize(
    "chunks", [[], [StreamChunk("", "content")], [StreamChunk("reason <&>", "reason")]]
)
async def test_empty_or_reason_only_stream_never_edits_empty_text(
    chunks: list[StreamChunk],
) -> None:
    recorder = MessageRecorder()
    message = recorder.make_message()
    ticks = count(step=2)
    with patch(
        "handlers.user.chatgpt.answer.time.monotonic", side_effect=lambda: next(ticks)
    ):
        result = await AnswerHandler(event=message)._stream_to_message(
            message, response_stream(chunks)
        )
    assert result == ""
    assert message.html_text == "Модель не вернула ответ."
    assert all(visible_text(chunk) for chunk in recorder.emissions)


async def test_identical_updates_are_not_sent_again() -> None:
    recorder = MessageRecorder()
    message = recorder.make_message()
    ticks = count(step=2)
    with patch(
        "handlers.user.chatgpt.answer.time.monotonic", side_effect=lambda: next(ticks)
    ):
        await AnswerHandler(event=message)._stream_to_message(
            message,
            response_stream(
                [StreamChunk("hello", "content"), StreamChunk("reason", "reason")]
            ),
        )
    message.edit_text.assert_awaited_once()


def make_handler() -> tuple[AnswerHandler, FSMContext, list[str], MessageRecorder]:
    recorder = MessageRecorder()
    event = recorder.make_message("prompt")
    event.text = "prompt"
    event.photo = None
    event.caption = None
    state = FSMContext(MemoryStorage(), StorageKey(bot_id=1, chat_id=2, user_id=3))
    history: list[str] = []
    handler = AnswerHandler(event=event, state=state, data={"messages": history})
    return handler, state, history, recorder


@pytest.mark.parametrize(
    "failure", ["stream", "live_edit", "final_edit", "answer", "prompt"]
)
async def test_failed_response_always_restores_state(failure: str) -> None:
    handler, state, history, recorder = make_handler()
    error = TelegramBadRequest(
        method=EditMessageText(text="text"), message="edit failed"
    )

    async def stream(*args: Any) -> AsyncGenerator[StreamChunk]:
        if failure == "stream":
            yield StreamChunk("partial", "content")
            raise ConnectionError("stream failed")
        if failure == "final_edit":
            yield StreamChunk("", "content")
        yield StreamChunk("a" * 4000, "content")

    original_make = recorder.make_message

    def make_failing_message(text: str = "Подождите") -> MagicMock:
        message = original_make(text)
        if failure in {"live_edit", "final_edit"}:
            message.edit_text.side_effect = error
        elif failure == "answer":
            message.answer.side_effect = error
        return message

    ticks = count(step=2 if failure != "final_edit" else 0)
    with (
        patch.object(recorder, "make_message", side_effect=make_failing_message),
        patch("handlers.user.chatgpt.answer.OpenRouter.stream", new=stream),
        patch(
            "handlers.user.chatgpt.answer.time.monotonic",
            side_effect=lambda: next(ticks),
        ),
    ):
        if failure == "prompt":
            with (
                patch.object(
                    handler, "_build_prompt", side_effect=ValueError("prompt failed")
                ),
                pytest.raises(ValueError, match="prompt failed"),
            ):
                await handler.handle()
        else:
            with pytest.raises(
                ConnectionError if failure == "stream" else TelegramBadRequest
            ):
                await handler.handle()

    assert await state.get_state() == FSM.get_message.state
    assert len(history) <= 1


async def test_success_keeps_complete_raw_response_in_history() -> None:
    handler, state, history, _recorder = make_handler()
    text = "```python\n" + "print('<&>😀')\n" * 500 + "```"
    with patch(
        "handlers.user.chatgpt.answer.OpenRouter.stream",
        return_value=response_stream([StreamChunk(text, "content")]),
    ):
        await handler.handle()
    assert history == ["prompt", text]
    assert await state.get_state() == FSM.get_message.state


async def test_cancelled_stream_restores_state() -> None:
    handler, state, history, _recorder = make_handler()

    async def stream(*args: Any) -> AsyncGenerator[StreamChunk]:
        assert await state.get_state() == FSM.finish.state
        yield StreamChunk("partial", "content")
        raise CancelledError

    with (
        patch("handlers.user.chatgpt.answer.OpenRouter.stream", new=stream),
        pytest.raises(CancelledError),
    ):
        await handler.handle()
    assert await state.get_state() == FSM.get_message.state
    assert history == ["prompt"]


async def test_missing_prompt_restores_state_without_starting_stream() -> None:
    handler, state, history, _recorder = make_handler()
    with (
        patch.object(handler, "_build_prompt", return_value=None),
        patch("handlers.user.chatgpt.answer.OpenRouter.stream") as stream,
    ):
        await handler.handle()
    stream.assert_not_called()
    assert await state.get_state() == FSM.get_message.state
    assert history == []
