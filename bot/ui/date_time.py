from time import time

from aiogram.utils.formatting import DateTime, Text


def format_date_time(unix_time: int, fallback: str) -> Text:
    """Render a known instant, keeping text for clients without date entities."""
    # Formatted date spans are limited to 31 UTF-16 units, with no nesting.
    if not fallback or len(fallback.encode("utf-16-le")) // 2 > 31:
        return Text(fallback)
    # Telegram only accepts dates from the Unix epoch through 1098 days ahead.
    if not 0 <= unix_time <= int(time()) + 1098 * 86400:
        return Text(fallback)
    return DateTime(fallback, unix_time=unix_time, date_time_format="dt")
