from datetime import date, time, timedelta

import pytest

from ui.components.remind_creator import RemindCreator
from ui.date_time import format_date_time


@pytest.mark.parametrize(
    ("timestamp", "has_entity"),
    [(-1, False), (0, True), (1_894_867_200, True), (1_894_867_201, False)],
)
def test_date_entity_timestamp_limits(
    timestamp: int, has_entity: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Telegram permits the Unix epoch through 1098 days after this fixed now.
    monkeypatch.setattr("ui.date_time.time", lambda: 1_800_000_000)
    text, entities = format_date_time(timestamp, "01.01.1970 00:00").render()

    assert text == "01.01.1970 00:00"
    assert bool(entities) == has_entity


@pytest.mark.parametrize("fallback", ["", "📆" * 16, "x" * 32])
def test_unsupported_date_spans_keep_plain_text(fallback: str) -> None:
    assert format_date_time(0, fallback).render() == (fallback, [])


@pytest.mark.parametrize(
    ("selected_date", "selected_time", "tz", "readable_input"),
    [
        (date(2027, 1, 1), None, timedelta(0), "01.01.2027"),
        (None, time(0, 15), timedelta(0), "00:15"),
        (date(2027, 1, 1), time(0, 15), None, "01.01.2027 00:15"),
    ],
)
def test_incomplete_reminders_have_no_date_entity(
    selected_date: date | None,
    selected_time: time | None,
    tz: timedelta | None,
    readable_input: str,
) -> None:
    creator = RemindCreator(date=selected_date, time=selected_time, tz=tz)
    text, entities = creator.as_text().render()

    assert all(entity.type != "date_time" for entity in entities)
    assert readable_input in text


def test_legacy_html_render_keeps_readable_dates_and_escapes_input() -> None:
    creator = RemindCreator(
        text="Проверить <b>текст</b> & 📆",
        date=date(2027, 1, 1),
        time=time(0, 15),
        tz=timedelta(hours=5, minutes=30),
    )
    html = creator.render()

    assert "01.01.2027 00:15" in html
    assert "&lt;b&gt;текст&lt;/b&gt; &amp; 📆" in html
    assert "tg-time" not in html


def test_far_future_reminder_keeps_readable_date() -> None:
    text, entities = (
        RemindCreator(date=date(9999, 1, 1), time=time(12), tz=timedelta(0))
        .as_text()
        .render()
    )

    assert "01.01.9999 12:00 UTC+0000" in text
    assert all(entity.type != "date_time" for entity in entities)
