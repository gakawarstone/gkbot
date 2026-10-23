import asyncio
import json
import os
import subprocess
import sys
from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramNetworkError,
    TelegramNotFound,
    TelegramRetryAfter,
    TelegramServerError,
)
from aiogram.methods import SendRichMessage, SendRichMessageDraft, TelegramMethod
from aiogram.types import Chat, InputRichMessage, Message, RichMessage
from pydantic import ValidationError

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
    assert message.model_dump(exclude_none=True) == {
        "blocks": [
            {"type": "paragraph", "text": literal},
            {"type": "pre", "text": literal, "language": "python"},
            {"type": "mathematical_expression", "expression": r"\int_0^1 x^2\,dx"},
            {
                "type": "details",
                "summary": "Reasoning",
                "blocks": [{"type": "paragraph", "text": literal}],
            },
        ]
    }


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
    # Exercise validation of the wire representation, not just model instances.
    assert (
        InputRichMessage.model_validate_json(
            to_rich_message(parts, draft=draft).model_dump_json()
        ).model_dump(exclude_none=True)
        == data
    )


@pytest.mark.parametrize(
    ("parts", "limits"),
    [
        ((), RichMessageLimits()),
        ((TextPart("a"), TextPart("b")), RichMessageLimits(max_nodes=1)),
        ((ReasoningPart("a"),), RichMessageLimits(max_nodes=1)),
        ((ReasoningPart("a"),), RichMessageLimits(max_depth=1)),
        ((TextPart("😀" * 10),), RichMessageLimits(max_payload_bytes=39)),
        ((TextPart("x"),), RichMessageLimits(max_payload_bytes=10)),
        ((TextPart("\ud800"),), RichMessageLimits()),
        ((ListPart(((TextPart("x"),),), start=0),), RichMessageLimits()),
        ((ListPart(((),) * 1001),), RichMessageLimits()),
    ],
)
def test_invalid_or_over_budget_response_is_rejected(
    parts: ResponseParts, limits: RichMessageLimits
) -> None:
    with pytest.raises(RichMessageConversionError):
        to_rich_message(parts, limits=limits)


@pytest.mark.parametrize("field", ["max_depth", "max_nodes", "max_payload_bytes"])
def test_budgets_must_be_positive(field: str) -> None:
    with pytest.raises(ValueError, match="positive"):
        RichMessageLimits(**{field: 0})


def test_deep_tree_is_rejected_before_recursive_conversion() -> None:
    parts: ResponseParts = (TextPart("deep"),)
    for _ in range(2000):
        parts = (DetailsPart("details", parts),)
    with (
        patch("services.rich_messages._convert_part") as convert,
        pytest.raises(RichMessageConversionError),
    ):
        to_rich_message(parts)
    convert.assert_not_called()


def test_large_valid_response_and_maximum_nesting() -> None:
    parts: ResponseParts = tuple(TextPart("😀 <&>" * 100) for _ in range(100))
    for _ in range(15):
        parts = (DetailsPart("details", parts),)
    message = to_rich_message(parts)
    dumped = message.model_dump_json(exclude_none=True)
    assert dumped.count("paragraph") == 100
    assert InputRichMessage.model_validate_json(dumped) == message


def test_payload_budget_includes_json_unicode_escapes() -> None:
    parts = (TextPart("😀 Привет"),)
    message = to_rich_message(parts)
    payload = json.dumps(message.model_dump(mode="json", exclude_none=True))
    size = len(payload.encode("utf-8"))
    assert to_rich_message(parts, limits=RichMessageLimits(max_payload_bytes=size)) == (
        message
    )
    with pytest.raises(RichMessageConversionError, match="JSON"):
        to_rich_message(parts, limits=RichMessageLimits(max_payload_bytes=size - 1))


def test_benchmark_and_nested_validation_finish_within_timeout() -> None:
    root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tests.benchmarks.rich_messages",
            "--iterations",
            "1",
        ],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(root / "bot")},
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    report = json.loads(result.stdout)
    nested = next(r for r in report["results"] if r["fixture"] == "nested_16")
    assert nested["rich"]["payload_bytes"] > 0


class RecordingSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.requests: list[TelegramMethod[Any]] = []
        self.failure: Callable[[TelegramMethod[Any]], TelegramAPIError] | None = None
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
        if self.failure is not None:
            raise self.failure(method)
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


def make_prototype(
    *,
    enabled: bool = True,
    chat_type: str = "private",
    supported: bool | None = None,
    business: str | None = None,
) -> tuple[RichMessagePrototype, RecordingSession]:
    session = RecordingSession()
    bot = Bot("123456:TEST", session=session)
    source = Message(
        message_id=100,
        date=datetime.now(UTC),
        chat=Chat(id=123, type=chat_type),
        message_thread_id=42,
        is_topic_message=False,
        business_connection_id=business,
    )
    return RichMessagePrototype(
        bot, source, enabled=enabled, server_supports_rich=supported
    ), session


@pytest.mark.parametrize("draft", [True, False])
async def test_successful_rich_delivery_preserves_context(draft: bool) -> None:
    prototype, session = make_prototype()
    fallback = AsyncMock()
    parts = (ReasoningPart("why"), CodePart("print('<&>')", "python"))
    if draft:
        assert await prototype.send_draft(parts, 1234, fallback) is True
        assert await prototype.send_draft(parts, 1234, fallback) is True
    else:
        result = await prototype.send(parts, fallback)
        assert result.rich_message is not None
    fallback.assert_not_awaited()
    for method in session.requests:
        assert isinstance(method, (SendRichMessage, SendRichMessageDraft))
        assert method.chat_id == 123 and method.message_thread_id == 42
        payload = method.model_dump(exclude_none=True)
        assert "html" not in payload["rich_message"]
        assert "markdown" not in payload["rich_message"]
        assert "parse_mode" not in payload
        prepared = session.prepare_value(method.rich_message, prototype.bot, files={})
        assert prepared == json.dumps(
            method.rich_message.model_dump(mode="json", exclude_none=True)
        )
        if isinstance(method, SendRichMessageDraft):
            assert method.draft_id == 1234
            assert method.can_stop is True and method.keep_on_stop is False
            assert payload["rich_message"]["blocks"][0]["type"] == "thinking"
        else:
            assert method.reply_parameters is not None
            assert method.reply_parameters.message_id == 100
            assert payload["rich_message"]["blocks"][0]["type"] == "details"


async def test_prototype_is_disabled_by_default() -> None:
    enabled, session = make_prototype()
    prototype = RichMessagePrototype(enabled.bot, enabled.source)
    fallback = AsyncMock(return_value=enabled.source)
    assert await prototype.send((TextPart("hello"),), fallback) is enabled.source
    fallback.assert_awaited_once()
    assert not session.requests


@pytest.mark.parametrize("draft", [True, False])
@pytest.mark.parametrize(
    "options",
    [
        {"enabled": False},
        {"supported": False},
        {"chat_type": "group"},
        {"chat_type": "supergroup"},
        {"chat_type": "channel"},
        {"business": "business-id"},
    ],
)
async def test_ineligible_chat_or_server_uses_fallback(
    draft: bool, options: dict[str, Any]
) -> None:
    prototype, session = make_prototype(**options)
    expected = False if draft else prototype.source
    fallback = AsyncMock(return_value=expected)
    if draft:
        result = await prototype.send_draft((TextPart("hello"),), 1, fallback)
    else:
        result = await prototype.send((TextPart("hello"),), fallback)
    assert result is expected
    fallback.assert_awaited_once()
    assert not session.requests


@pytest.mark.parametrize("draft", [True, False])
@pytest.mark.parametrize("invalid", [True, False])
async def test_conversion_failure_uses_fallback(draft: bool, invalid: bool) -> None:
    prototype, session = make_prototype()
    fallback = AsyncMock(return_value=prototype.source)
    if invalid:
        error: Exception = ValidationError.from_exception_data("parts", [])
    else:
        error = RichMessageConversionError("budget exceeded")
    with patch("services.rich_messages.to_rich_message", side_effect=error):
        if draft:
            await prototype.send_draft((TextPart("original"),), 1, fallback)
        else:
            await prototype.send((TextPart("original"),), fallback)
    fallback.assert_awaited_once()
    assert not session.requests


@pytest.mark.parametrize("draft", [True, False])
@pytest.mark.parametrize("error_type", [TelegramBadRequest, TelegramNotFound])
async def test_explicit_api_rejection_falls_back_once(
    draft: bool, error_type: type[TelegramAPIError]
) -> None:
    prototype, session = make_prototype()
    session.failure = lambda method: error_type(method, "unsupported")
    fallback = AsyncMock(return_value=prototype.source)
    if draft:
        await prototype.send_draft((TextPart("hello"),), 1, fallback)
    else:
        await prototype.send((TextPart("hello"),), fallback)
    assert len(session.requests) == 1
    fallback.assert_awaited_once()


async def test_draft_failure_selects_html_for_remaining_generation() -> None:
    prototype, session = make_prototype()
    session.failure = lambda method: TelegramNotFound(method, "unsupported")
    preview = AsyncMock(return_value=True)
    final = AsyncMock(return_value=prototype.source)
    assert await prototype.send_draft((TextPart("first"),), 7, preview) is True
    assert await prototype.send_draft((TextPart("second"),), 7, preview) is True
    assert await prototype.send((TextPart("complete"),), final) is prototype.source
    assert len(session.requests) == 1
    assert preview.await_count == 2
    final.assert_awaited_once()


@pytest.mark.parametrize("draft", [True, False])
async def test_rate_limit_waits_before_fallback(draft: bool) -> None:
    prototype, session = make_prototype()
    session.failure = lambda method: TelegramRetryAfter(method, "slow down", 3)
    calls: list[str] = []

    async def cooldown(seconds: float) -> None:
        assert seconds == 3
        calls.append("cooldown")

    async def fallback() -> Any:
        calls.append("fallback")
        return False if draft else prototype.source

    with patch("services.rich_messages.asyncio.sleep", side_effect=cooldown):
        if draft:
            await prototype.send_draft((TextPart("hello"),), 1, fallback)
        else:
            await prototype.send((TextPart("hello"),), fallback)
    assert calls == ["cooldown", "fallback"]


@pytest.mark.parametrize("error_type", [TelegramNetworkError, TelegramServerError])
async def test_ambiguous_final_send_propagates_without_duplicate(
    error_type: type[TelegramAPIError],
) -> None:
    prototype, session = make_prototype()
    session.failure = lambda method: error_type(method, "connection lost")
    fallback = AsyncMock()
    with pytest.raises(error_type):
        await prototype.send((TextPart("hello"),), fallback)
    fallback.assert_not_awaited()
    # Drafts are temporary, so the same failure can safely select HTML fallback.
    assert (
        await prototype.send_draft(
            (TextPart("hello"),), 1, AsyncMock(return_value=False)
        )
        is False
    )


async def test_fallback_error_is_not_retried_or_swallowed() -> None:
    prototype, session = make_prototype(supported=False)
    fallback = AsyncMock(side_effect=RuntimeError("fallback failed"))
    with pytest.raises(RuntimeError, match="fallback failed"):
        await prototype.send((TextPart("hello"),), fallback)
    fallback.assert_awaited_once()
    assert not session.requests


@pytest.mark.parametrize("draft", [True, False])
async def test_cancellation_propagates_without_running_fallback(draft: bool) -> None:
    prototype, session = make_prototype()
    session.block = asyncio.Event()
    fallback = AsyncMock()
    if draft:
        operation = prototype.send_draft((TextPart("hello"),), 1, fallback)
    else:
        operation = prototype.send((TextPart("hello"),), fallback)
    task = asyncio.create_task(operation)
    await asyncio.wait_for(session.started.wait(), timeout=1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    fallback.assert_not_awaited()


async def test_zero_draft_id_is_a_caller_error() -> None:
    prototype, session = make_prototype()
    fallback = AsyncMock()
    with pytest.raises(ValueError, match="non-zero"):
        await prototype.send_draft((TextPart("hello"),), 0, fallback)
    fallback.assert_not_awaited()
    assert not session.requests
