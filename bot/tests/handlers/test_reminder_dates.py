from datetime import UTC, date, datetime, time, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from aiogram.types import Chat, Message, User
from tortoise import Tortoise

from configs.db import MODELS
from handlers.user.reminder.create import CreateRemindHandler
from services.schedule import Schedule, TasksStorage


@pytest.mark.parametrize("offset_hours", [-12, -3.5, 0, 5.5, 14])
async def test_confirmation_entity_matches_stored_instant(
    offset_hours: float, monkeypatch: pytest.MonkeyPatch
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
    expected = datetime.combine(selected_date, selected_time, timezone(selected_offset))
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

    assert len(stored) == 1
    assert stored[0][1].timestamp() == expected.timestamp()
    edit_text.assert_awaited_once()
    payload = edit_text.call_args.kwargs
    assert payload["parse_mode"] is None
    assert "Проверить 🧑‍💻 <b>отчёт</b> & план" in payload["text"]
    entity = next(
        entity for entity in payload["entities"] if entity.type == "date_time"
    )
    assert entity.unix_time == int(expected.timestamp())
    assert entity.date_time_format == "dt"
    encoded = payload["text"].encode("utf-16-le")
    date_span = encoded[entity.offset * 2 : (entity.offset + entity.length) * 2].decode(
        "utf-16-le"
    )
    assert date_span == expected.strftime("%d.%m.%Y %H:%M UTC%z")
    assert "Создано успешно" in payload["text"]
    success_entity = payload["entities"][-1]
    assert success_entity.type == "underline"
    assert (
        encoded[
            success_entity.offset * 2 : (success_entity.offset + success_entity.length)
            * 2
        ].decode("utf-16-le")
        == "Создано успешно"
    )
    assert all(
        other == entity
        or other.offset + other.length <= entity.offset
        or other.offset >= entity.offset + entity.length
        for other in payload["entities"]
    )
