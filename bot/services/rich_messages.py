"""Opt-in rich-message experiment, independent of the production AI handler.

The caller supplies semantic response parts and owns the original model text,
stream lifetime, cancellation registration, and the existing HTML fallback.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from aiogram import Bot
from aiogram.enums import ChatType
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)
from aiogram.methods import SendRichMessage, SendRichMessageDraft, TelegramMethod
from aiogram.types import (
    InputRichBlockBlockQuotation,
    InputRichBlockDetails,
    InputRichBlockList,
    InputRichBlockListItem,
    InputRichBlockMathematicalExpression,
    InputRichBlockParagraph,
    InputRichBlockPreformatted,
    InputRichBlockThinking,
    InputRichMessage,
    Message,
    ReplyParameters,
)
from aiogram.types.input_rich_block_union import InputRichBlockUnion
from pydantic import ValidationError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TextPart:
    text: str


@dataclass(frozen=True, slots=True)
class CodePart:
    text: str
    language: str | None = None


@dataclass(frozen=True, slots=True)
class MathPart:
    expression: str


@dataclass(frozen=True, slots=True)
class ReasoningPart:
    text: str


@dataclass(frozen=True, slots=True)
class QuotePart:
    blocks: tuple[ResponsePart, ...]
    credit: str | None = None


@dataclass(frozen=True, slots=True)
class DetailsPart:
    summary: str
    blocks: tuple[ResponsePart, ...]
    is_open: bool = False


@dataclass(frozen=True, slots=True)
class ListPart:
    items: tuple[tuple[ResponsePart, ...], ...]
    start: int | None = None


type ResponsePart = (
    TextPart | CodePart | MathPart | ReasoningPart | QuotePart | DetailsPart | ListPart
)
type ResponseParts = tuple[ResponsePart, ...]


@dataclass(frozen=True, slots=True)
class RichMessageLimits:
    """Application budgets, not Telegram's undocumented rich-message limits."""

    max_depth: int = 16
    max_nodes: int = 1000
    max_payload_bytes: int = 256 * 1024

    def __post_init__(self) -> None:
        if min(self.max_depth, self.max_nodes, self.max_payload_bytes) < 1:
            raise ValueError("Rich message budgets must be positive")


class RichMessageConversionError(ValueError):
    """The response cannot be represented within the prototype budgets."""


DEFAULT_RICH_MESSAGE_LIMITS = RichMessageLimits()


def _check_parts(
    parts: ResponseParts, limits: RichMessageLimits, *, draft: bool
) -> None:
    # Walk iteratively before calling recursive Pydantic constructors. This also
    # rejects cycles and excessive width before allocating a converted tree.
    if len(parts) > limits.max_nodes:
        raise RichMessageConversionError("Too many rich blocks")
    pending = [(part, 1) for part in parts]
    nodes = 0
    text_size = 0
    while pending:
        part, depth = pending.pop()
        nodes += 1
        child_groups: tuple[ResponseParts, ...] = ()
        texts: tuple[str, ...]
        match part:
            case TextPart(text):
                texts = (text,)
            case ReasoningPart(text):
                texts = (text,)
                if not draft:
                    nodes += 1
                    depth += 1
            case CodePart(text, language):
                texts = (text, language or "")
            case MathPart(expression):
                texts = (expression,)
            case QuotePart(blocks, credit):
                child_groups, texts = (blocks,), (credit or "",)
            case DetailsPart(summary, blocks):
                child_groups, texts = (blocks,), (summary,)
            case ListPart(items, start):
                nodes += len(items)  # List items also occupy the payload tree.
                if start is not None and start < 1:
                    raise RichMessageConversionError("Invalid or oversized rich list")
                child_groups = items
                texts = ()
            case _:
                raise RichMessageConversionError("Unsupported response part")
        if depth > limits.max_depth or nodes + len(pending) > limits.max_nodes:
            raise RichMessageConversionError("Rich block tree exceeds budgets")
        for children in child_groups:
            if len(children) + nodes + len(pending) > limits.max_nodes:
                raise RichMessageConversionError("Too many rich blocks")
            pending.extend((child, depth + 1) for child in children)
        for text in texts:
            # len() first avoids encoding an arbitrarily large string.
            if not isinstance(text, str) or len(text) > limits.max_payload_bytes:
                raise RichMessageConversionError("Invalid or oversized rich text")
            try:
                text_size += len(text.encode("utf-8"))
            except UnicodeEncodeError as error:
                raise RichMessageConversionError(
                    "Invalid Unicode in rich text"
                ) from error
            if text_size > limits.max_payload_bytes:
                raise RichMessageConversionError("Rich text exceeds payload budget")


def _convert_part(part: ResponsePart, *, draft: bool) -> InputRichBlockUnion:
    match part:
        case TextPart(text):
            return InputRichBlockParagraph(text=text)
        case CodePart(text, language):
            return InputRichBlockPreformatted(text=text, language=language)
        case MathPart(expression):
            return InputRichBlockMathematicalExpression(expression=expression)
        case ReasoningPart(text):
            if draft:
                return InputRichBlockThinking(text=text)
            return InputRichBlockDetails(
                summary="Reasoning", blocks=[InputRichBlockParagraph(text=text)]
            )
        case QuotePart(blocks, credit):
            return InputRichBlockBlockQuotation(
                blocks=[_convert_part(child, draft=draft) for child in blocks],
                credit=credit,
            )
        case DetailsPart(summary, blocks, is_open):
            return InputRichBlockDetails(
                summary=summary,
                blocks=[_convert_part(child, draft=draft) for child in blocks],
                is_open=is_open or None,
            )
        case ListPart(items, start):
            return InputRichBlockList(
                items=[
                    InputRichBlockListItem(
                        blocks=[_convert_part(child, draft=draft) for child in item],
                        value=start + index if start is not None else None,
                        type="1" if start is not None else None,
                    )
                    for index, item in enumerate(items)
                ]
            )
    raise RichMessageConversionError("Unsupported response part")


def to_rich_message(
    parts: ResponseParts,
    *,
    draft: bool = False,
    limits: RichMessageLimits = DEFAULT_RICH_MESSAGE_LIMITS,
) -> InputRichMessage:
    """Convert semantic parts to native blocks without Markdown or HTML parsing."""
    if not parts:
        raise RichMessageConversionError("An empty response needs the HTML fallback")
    _check_parts(parts, limits, draft=draft)
    message = InputRichMessage(
        blocks=[_convert_part(part, draft=draft) for part in parts]
    )
    # Match aiogram's default JSON serializer, including ASCII escapes. UTF-8
    # model_dump_json() can underestimate its wire size for non-ASCII text.
    # Default json.dumps produces ASCII, so its character count is its byte size.
    payload = json.dumps(message.model_dump(mode="json", exclude_none=True))
    if len(payload) > limits.max_payload_bytes:
        raise RichMessageConversionError("Rich JSON exceeds payload budget")
    return message


class RichMessagePrototype:
    """Send opt-in private-chat rich messages, delegating HTML to the caller.

    A draft failure may switch to the existing streaming path via the callback.
    Final network/5xx errors propagate because the message may already exist.
    No model requests, FSM mutations, context storage, or stop registration live
    here. The caller must use the existing generation lifecycle for streaming.
    """

    def __init__(
        self,
        bot: Bot,
        source: Message,
        *,
        enabled: bool = False,
        server_supports_rich: bool | None = None,
        limits: RichMessageLimits = DEFAULT_RICH_MESSAGE_LIMITS,
    ) -> None:
        self.bot = bot
        self.source = source
        self.enabled = enabled
        self.server_supports_rich = server_supports_rich
        self.limits = limits
        self._fallback_only = False

    def _message(
        self, parts: ResponseParts, *, draft: bool = False
    ) -> InputRichMessage | None:
        if (
            not self.enabled
            or self._fallback_only
            or self.server_supports_rich is False
            or self.source.chat.type != ChatType.PRIVATE
            or self.source.business_connection_id is not None
        ):
            return None
        try:
            return to_rich_message(parts, draft=draft, limits=self.limits)
        except (RichMessageConversionError, ValidationError):
            self._fallback_only = True
            logger.info("Rich conversion failed; using the existing HTML path")
            return None

    async def send(
        self, parts: ResponseParts, fallback: Callable[[], Awaitable[Message]]
    ) -> Message:
        message = self._message(parts)
        if message is None:
            return await fallback()
        return await self._deliver(
            SendRichMessage(
                chat_id=self.source.chat.id,
                message_thread_id=self.source.message_thread_id,
                reply_parameters=ReplyParameters(message_id=self.source.message_id),
                rich_message=message,
            ),
            fallback,
        )

    async def send_draft(
        self,
        parts: ResponseParts,
        draft_id: int,
        fallback: Callable[[], Awaitable[bool]],
    ) -> bool:
        if draft_id == 0:
            raise ValueError("The draft ID must be non-zero")
        message = self._message(parts, draft=True)
        if message is None:
            return await fallback()
        return await self._deliver(
            SendRichMessageDraft(
                chat_id=self.source.chat.id,
                message_thread_id=self.source.message_thread_id,
                draft_id=draft_id,
                rich_message=message,
                can_stop=True,
                keep_on_stop=False,
            ),
            fallback,
        )

    async def _deliver[T](
        self, method: TelegramMethod[T], fallback: Callable[[], Awaitable[T]]
    ) -> T:
        try:
            return await self.bot(method)
        except TelegramAPIError as error:
            if isinstance(method, SendRichMessage) and isinstance(
                error, (TelegramNetworkError, TelegramServerError)
            ):
                raise
            logger.warning("Rich send failed: %s; using HTML", type(error).__name__)
            self._fallback_only = True
            if isinstance(error, TelegramRetryAfter):
                await asyncio.sleep(error.retry_after)
        return await fallback()
