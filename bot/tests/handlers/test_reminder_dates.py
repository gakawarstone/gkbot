from datetime import UTC, date, datetime, time, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from aiogram.types import Chat, Message, User
from tortoise import Tortoise

from configs.db import MODELS
from handlers.user.reminder.create import CreateRemindHandler
from services.schedule import Schedule, TasksStorage


@pytest.mark.parametrize(
    ("offset_hours", "expected_timestamp", "expected_fallback"),
    [
        (-12, 1_798_805_700, "01.01.2027 00:15 UTC-1200"),
        (-3.5, 1_798_775_100, "01.01.2027 00:15 UTC-0330"),
        (0, 1_798_762_500, "01.01.2027 00:15 UTC+0000"),
        (5.5, 1_798_742_700, "01.01.2027 00:15 UTC+0530"),
        (14, 1_798_712_100, "01.01.2027 00:15 UTC+1400"),
    ],
)
async def test_confirmation_entity_matches_stored_instant(
    offset_hours: float,
    expected_timestamp: int,
    expected_fallback: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    message = Message(
        message_id=42,
        date=datetime(2026, 10, 23, tzinfo=UTC),
        chat=Chat(id=42, type="private"),
        from_user=User(id=1, is_bot=False, first_name="Test"),
    )
    edit_text = AsyncMock()
    monkeypatch.setattr(Message, "edit_text", edit_text)
    # The server's timezone must not influence the displayed or stored instant.
    monkeypatch.setattr(Schedule, "get_local_tz", lambda: timezone(timedelta(hours=-7)))
    selected_date = date(2027, 1, 1)
    selected_time = time(0, 15)
    selected_offset = timedelta(hours=offset_hours)
    handler = CreateRemindHandler(
        message,
        data={
            "text": "Проверить 🧑‍💻 <b>отчёт</b> & план",
            "date": selected_date,
            "time": selected_time,
            "tz": selected_offset,
            "message": message,
        },
    )

    await Tortoise.init(db_url="sqlite://:memory:", modules={"models": MODELS})
    try:
        await Tortoise.generate_schemas(safe=True)
        await handler.handle()
        stored = await TasksStorage().get_all()
    finally:
        await Tortoise.close_connections()

    (stored_reminder,) = stored
    assert stored_reminder[1].timestamp() == expected_timestamp
    payload = edit_text.call_args.kwargs
    assert "Проверить 🧑‍💻 <b>отчёт</b> & план" in payload["text"]
    entity = next(
        entity for entity in payload["entities"] if entity.type == "date_time"
    )
    assert entity.unix_time == stored_reminder[1].timestamp()
    encoded = payload["text"].encode("utf-16-le")
    date_span = encoded[entity.offset * 2 : (entity.offset + entity.length) * 2].decode(
        "utf-16-le"
    )
    assert date_span == expected_fallback
    assert all(
        other == entity
        or other.offset + other.length <= entity.offset
        or other.offset >= entity.offset + entity.length
        for other in payload["entities"]
    )
