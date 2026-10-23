from datetime import date, time, timedelta

import pytest
from aiogram.utils.formatting import Text, Underline

from ui.components.remind_creator import RemindCreator
from ui.date_time import format_date_time


def test_date_entity_offsets_with_cyrillic_and_emoji() -> None:
    prefix = "Напоминание 🧑‍💻: "
    fallback = "01.01.2027 00:15 UTC+0530"
    content = Text(
        prefix,
        format_date_time(1798742700, fallback),
        "\n",
        Underline("Создано ✅"),
    )
    text, entities = content.render()
    entity, status = entities

    assert text == prefix + fallback + "\nСоздано ✅"
    assert entity.type == "date_time"
    assert entity.unix_time == 1798742700
    assert entity.date_time_format == "dt"
    assert entity.offset == len(prefix.encode("utf-16-le")) // 2
    assert entity.length == len(fallback.encode("utf-16-le")) // 2
    assert status.offset == len((prefix + fallback + "\n").encode("utf-16-le")) // 2
    assert content.as_kwargs()["parse_mode"] is None


@pytest.mark.parametrize("offset", [-1, 0, 1098 * 86400, 1098 * 86400 + 1])
def test_date_entity_timestamp_limits(
    offset: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("ui.date_time.time", lambda: 0)
    text, entities = format_date_time(offset, "01.01.1970 00:00").render()

    assert text == "01.01.1970 00:00"
    assert bool(entities) == (0 <= offset <= 1098 * 86400)


@pytest.mark.parametrize("fallback", ["", "📆" * 16, "x" * 32])
def test_unsupported_date_spans_keep_plain_text(fallback: str) -> None:
    assert format_date_time(0, fallback).render() == (fallback, [])


@pytest.mark.parametrize(
    ("selected_date", "selected_time", "tz"),
    [
        (None, None, None),
        (date(2027, 1, 1), None, timedelta(0)),
        (None, time(0, 15), timedelta(0)),
        (date(2027, 1, 1), time(0, 15), None),
    ],
)
def test_incomplete_reminders_have_no_date_entity(
    selected_date: date | None, selected_time: time | None, tz: timedelta | None
) -> None:
    creator = RemindCreator(date=selected_date, time=selected_time, tz=tz)
    text, entities = creator.as_text().render()

    assert all(entity.type != "date_time" for entity in entities)
    assert "Время: " in text
    if selected_date is not None:
        assert "01.01.2027" in text
    if selected_time is not None:
        assert "00:15" in text
    assert creator.as_text().render() == (text, entities)


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
