from contextlib import aclosing

import pytest
from aiogram.exceptions import TelegramNotFound
from aiogram.methods import SendRichMessage
from aiogram.types import InputRichMessage, Message
from aiogram.utils.formatting import sizeof

from extensions.handlers.message.markdown_render import parse_markdown
from services.rich_messages import RichMessageLimits, RichMessagePrototype, TextPart
from tests.handlers.test_chatgpt_drafts import chunks_stream, make_handler, visible_text


@pytest.mark.parametrize("rejected_by_server", [True, False])
async def test_rich_failure_preserves_full_response_in_existing_html_path(
    rejected_by_server: bool,
) -> None:
    handler, session, _, _ = make_handler(thread_id=42)
    original = "**Привет <&> 😀**\n\n```python\nprint('<&>')\n```\n\n" * 300
    limits = RichMessageLimits(
        max_payload_bytes=256 * 1024 if rejected_by_server else 100
    )
    prototype = RichMessagePrototype(
        handler.bot,
        handler.event,
        enabled=True,
        limits=limits,
    )
    if rejected_by_server:
        session.failures[1] = TelegramNotFound(
            SendRichMessage(chat_id=123, rich_message=InputRichMessage(blocks=[])),
            "method not found",
        )
    calls = 0

    async def fallback() -> Message:
        nonlocal calls
        calls += 1
        message = await handler._answer("Подождите")
        async with aclosing(chunks_stream(original)) as stream:
            assert await handler._stream_to_message(message, stream) == original
        return message

    await prototype.send((TextPart(original),), fallback)
    assert calls == 1
    assert len([r for r in session.requests if isinstance(r, SendRichMessage)]) == (
        1 if rejected_by_server else 0
    )
    assert (
        "".join(visible_text(m.text or "") for m in session.messages.values())
        == (parse_markdown(original).render()[0])
    )
    assert all(
        sizeof(visible_text(m.text or "")) <= 1500 for m in session.messages.values()
    )
    assert all(m.message_thread_id == 42 for m in session.messages.values())
