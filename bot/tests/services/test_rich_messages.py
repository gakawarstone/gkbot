import asyncio
import json
import os
import subprocess
import sys
from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramNetworkError,
    TelegramNotFound,
    TelegramRetryAfter,
    TelegramServerError,
)
from aiogram.methods import (
    SendMessage,
    SendMessageDraft,
    SendRichMessage,
    SendRichMessageDraft,
    TelegramMethod,
)
from aiogram.types import Chat, Message, RichMessage

from services.rich_messages import (
    CodePart,
    DetailsPart,
    ListPart,
    MathPart,
    QuotePart,
    ReasoningPart,
    ResponseParts,
    RichMessageConversionError,
    RichMessageLimits,
    RichMessagePrototype,
    TextPart,
    to_rich_message,
)


def test_native_blocks_preserve_literal_model_text() -> None:
    literal = "Привет <>& `**` 😀\nsecond line"
    message = to_rich_message(
        (
            TextPart(literal),
            CodePart(literal, "python"),
            MathPart(r"\int_0^1 x^2\,dx"),
            ReasoningPart(literal),
        )
    )
    blocks = message.model_dump(exclude_none=True)["blocks"]
    assert blocks[0] == {"type": "paragraph", "text": literal}
    assert blocks[1] == {"type": "pre", "text": literal, "language": "python"}
    assert blocks[2] == {
        "type": "mathematical_expression",
        "expression": r"\int_0^1 x^2\,dx",
    }
    assert blocks[3]["blocks"][0]["text"] == literal


@pytest.mark.parametrize("draft", [True, False])
def test_nested_lists_quotes_details_and_reasoning(draft: bool) -> None:
    parts = (
        QuotePart(
            (
                ListPart(
                    (
                        (TextPart("first"),),
                        (
                            DetailsPart(
                                "show <details>",
                                (ReasoningPart("because"), MathPart("x^2")),
                                is_open=True,
                            ),
                        ),
                    ),
                    start=3,
                ),
                ListPart(((CodePart("a < b"),),)),
            ),
            credit="author",
        ),
    )
    data = to_rich_message(parts, draft=draft).model_dump(exclude_none=True)
    quote = data["blocks"][0]
    assert quote["type"] == "blockquote" and quote["credit"] == "author"
    ordered = quote["blocks"][0]["items"]
    assert [item["value"] for item in ordered] == [3, 4]
    assert all(item["type"] == "1" for item in ordered)
    details = ordered[1]["blocks"][0]
    assert details["summary"] == "show <details>" and details["is_open"] is True
    assert details["blocks"][0]["type"] == ("thinking" if draft else "details")
    assert details["blocks"][1]["expression"] == "x^2"
    assert quote["blocks"][1]["items"] == [
        {"blocks": [{"type": "pre", "text": "a < b"}]}
    ]


@pytest.mark.parametrize(
    ("parts", "limits"),
    [
        ((TextPart("a"), TextPart("b")), RichMessageLimits(max_nodes=1)),
        ((ReasoningPart("a"),), RichMessageLimits(max_nodes=1)),
        ((ReasoningPart("a"),), RichMessageLimits(max_depth=1)),
        ((TextPart("\ud800"),), RichMessageLimits()),
        ((ListPart(((),) * 1001),), RichMessageLimits()),
    ],
)
def test_invalid_or_over_budget_response_is_rejected(
    parts: ResponseParts, limits: RichMessageLimits
) -> None:
    with pytest.raises(RichMessageConversionError):
        to_rich_message(parts, limits=limits)


def test_deep_tree_is_rejected_before_recursive_conversion() -> None:
    parts: ResponseParts = (TextPart("deep"),)
    for _ in range(2000):
        parts = (DetailsPart("details", parts),)
    with pytest.raises(RichMessageConversionError):
        to_rich_message(parts)


def test_large_valid_response_and_maximum_nesting() -> None:
    literal = "😀 <&>" * 100
    parts: ResponseParts = tuple(TextPart(literal) for _ in range(100))
    for _ in range(15):
        parts = (DetailsPart("details", parts),)
    message = to_rich_message(parts)
    blocks = message.model_dump(exclude_none=True)["blocks"]
    for _ in range(15):
        blocks = blocks[0]["blocks"]
    assert [block["text"] for block in blocks] == [literal] * 100


def test_payload_budget_includes_json_unicode_escapes() -> None:
    parts = (TextPart("😀 Привет"),)
    message = to_rich_message(parts)
    payload = json.dumps(message.model_dump(mode="json", exclude_none=True))
    size = len(payload.encode("utf-8"))
    assert to_rich_message(parts, limits=RichMessageLimits(max_payload_bytes=size)) == (
        message
    )
    with pytest.raises(RichMessageConversionError):
        to_rich_message(parts, limits=RichMessageLimits(max_payload_bytes=size - 1))


def test_nested_conversion_finishes_within_timeout() -> None:
    root = Path(__file__).resolve().parents[3]
    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from services.rich_messages import DetailsPart, TextPart, to_rich_message\n"
                "parts = (TextPart('Привет 😀'),)\n"
                "for _ in range(15):\n"
                "    parts = (DetailsPart('More', parts),)\n"
                "to_rich_message(parts).model_dump_json()\n"
            ),
        ],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(root / "bot")},
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )


class RecordingSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.requests: list[TelegramMethod[Any]] = []
        self.failure: (
            Callable[[TelegramMethod[Any]], TelegramAPIError | None] | None
        ) = None
        self.started = asyncio.Event()
        self.block: asyncio.Event | None = None

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
        self.started.set()
        if self.block is not None:
            await self.block.wait()
        if self.failure is not None and (error := self.failure(method)) is not None:
            raise error
        if isinstance(method, SendMessage):
            return Message(
                message_id=len(self.requests),
                date=datetime.now(UTC),
                chat=Chat(id=int(method.chat_id), type="private"),
                text=method.text,
            )
        if isinstance(method, SendRichMessage):
            return Message(
                message_id=101,
                date=datetime.now(UTC),
                chat=Chat(id=int(method.chat_id), type="private"),
                rich_message=RichMessage.model_validate(
                    method.rich_message.model_dump(exclude_none=True)
                ),
            )
        return True


def make_prototype() -> tuple[RichMessagePrototype, RecordingSession]:
    session = RecordingSession()
    bot = Bot("123456:TEST", session=session)
    source = Message(
        message_id=100,
        date=datetime.now(UTC),
        chat=Chat(id=123, type="private"),
        message_thread_id=42,
        is_topic_message=False,
    )
    return RichMessagePrototype(bot, source, enabled=True), session


@pytest.mark.parametrize("draft", [True, False])
async def test_successful_rich_delivery_preserves_context(draft: bool) -> None:
    prototype, session = make_prototype()

    async def fallback() -> Any:
        return await prototype.bot.send_message(chat_id=123, text="HTML fallback")

    parts = (ReasoningPart("why"), CodePart("print('<&>')", "python"))
    if draft:
        assert await prototype.send_draft(parts, 1234, fallback) is True
        assert await prototype.send_draft(parts, 1234, fallback) is True
    else:
        result = await prototype.send(parts, fallback)
        assert result.rich_message is not None
    for method in session.requests:
        assert isinstance(method, (SendRichMessage, SendRichMessageDraft))
        assert method.chat_id == 123 and method.message_thread_id == 42
        payload = method.model_dump(exclude_none=True)
        assert "html" not in payload["rich_message"]
        assert "markdown" not in payload["rich_message"]
        assert "parse_mode" not in payload
        if isinstance(method, SendRichMessageDraft):
            assert method.draft_id == 1234
            assert method.can_stop is True and method.keep_on_stop is False
            assert payload["rich_message"]["blocks"][0]["type"] == "thinking"
        else:
            assert method.reply_parameters is not None
            assert method.reply_parameters.message_id == 100
            assert payload["rich_message"]["blocks"][0]["type"] == "details"


async def test_draft_failure_selects_html_for_remaining_generation() -> None:
    prototype, session = make_prototype()
    session.failure = lambda method: (
        TelegramNotFound(cast(TelegramMethod[Any], method), "unsupported")
        if isinstance(method, (SendRichMessage, SendRichMessageDraft))
        else None
    )
    text = "first"

    async def preview() -> bool:
        return await prototype.bot.send_message_draft(
            chat_id=123, draft_id=7, text=text
        )

    async def final() -> Message:
        return await prototype.bot.send_message(chat_id=123, text="complete")

    assert await prototype.send_draft((TextPart("first"),), 7, preview) is True
    text = "second"
    assert await prototype.send_draft((TextPart("second"),), 7, preview) is True
    assert (await prototype.send((TextPart("complete"),), final)).text == "complete"
    assert [
        method.text
        for method in session.requests
        if isinstance(method, (SendMessageDraft, SendMessage))
    ] == ["first", "second", "complete"]
    assert (
        len([r for r in session.requests if isinstance(r, SendRichMessageDraft)]) == 1
    )


async def test_rate_limit_waits_before_fallback() -> None:
    prototype, session = make_prototype()
    session.failure = lambda method: (
        TelegramRetryAfter(method, "slow down", 3)
        if isinstance(method, SendRichMessageDraft)
        else None
    )
    calls: list[str] = []

    async def cooldown(seconds: float) -> None:
        assert seconds == 3
        calls.append("cooldown")

    async def fallback() -> bool:
        calls.append("fallback")
        return await prototype.bot.send_message_draft(
            chat_id=123, draft_id=1, text="original response"
        )

    with patch("services.rich_messages.asyncio.sleep", side_effect=cooldown):
        await prototype.send_draft((TextPart("original response"),), 1, fallback)
    assert calls == ["cooldown", "fallback"]
    assert isinstance(session.requests[-1], SendMessageDraft)
    assert session.requests[-1].text == "original response"


@pytest.mark.parametrize("error_type", [TelegramNetworkError, TelegramServerError])
async def test_ambiguous_final_send_propagates_without_duplicate(
    error_type: type[TelegramAPIError],
) -> None:
    prototype, session = make_prototype()
    session.failure = lambda method: error_type(method, "connection lost")

    async def fallback() -> Message:
        return await prototype.bot.send_message(chat_id=123, text="duplicate response")

    with pytest.raises(error_type):
        await prototype.send((TextPart("hello"),), fallback)
    assert len(session.requests) == 1
    assert not any(isinstance(r, SendMessage) for r in session.requests)


@pytest.mark.parametrize("draft", [True, False])
async def test_cancellation_propagates_without_running_fallback(draft: bool) -> None:
    prototype, session = make_prototype()
    session.block = asyncio.Event()

    async def fallback() -> Any:
        return await prototype.bot.send_message(chat_id=123, text="cancelled response")

    if draft:
        operation = prototype.send_draft((TextPart("hello"),), 1, fallback)
    else:
        operation = prototype.send((TextPart("hello"),), fallback)
    task = asyncio.create_task(operation)
    await asyncio.wait_for(session.started.wait(), timeout=1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, timeout=1)
    assert len(session.requests) == 1
    assert not any(isinstance(r, SendMessage) for r in session.requests)
