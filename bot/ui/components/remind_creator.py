from datetime import date, datetime, time, timedelta, timezone

from aiogram.utils.formatting import Bold, Text, Underline

from ui.date_time import format_date_time


class RemindCreator:
    def __init__(
        self,
        text: str | None = None,
        date: date | None = None,
        time: time | None = None,
        status_message: str | Text | None = None,
        tz: timedelta | None = None,
    ) -> None:
        self.text = text
        self.date = date
        self.time = time
        self.status_message = status_message
        self.tz = tz

    def as_text(self, *, localize: bool = True) -> Text:
        """Use date entities only when the reminder identifies a known instant."""
        has_highlight = False

        def render_property(value: str | None, prefix: str = "") -> Text:
            nonlocal has_highlight
            content = Text(prefix, value if value is not None else "...", " ")
            if value is None and not has_highlight:
                has_highlight = True
                return Text(Bold(" ", content), "👈")
            return content

        content = Text(
            Underline("Создатель напоминаний ⌚️"),
            "\n",
            render_property(self.text, "Текст: "),
            "\n",
        )
        if (
            localize
            and self.date is not None
            and self.time is not None
            and self.tz is not None
        ):
            # Match CreateRemindHandler.datetime without changing scheduling semantics.
            instant = datetime.combine(self.date, self.time, timezone(self.tz))
            fallback = instant.strftime("%d.%m.%Y %H:%M UTC%z")
            content += Text(
                "Время: ", format_date_time(int(instant.timestamp()), fallback), " \n"
            )
        else:
            content += Text(
                render_property(
                    self.date.strftime("%d.%m.%Y") if self.date else None, "Время: "
                ),
                render_property(self.time.strftime("%H:%M") if self.time else None),
                "\n",
            )
        if self.status_message is not None:
            content += Text(self.status_message, " ")
        return content

    def render(self) -> str:
        """Keep a readable HTML path for callers that cannot send date entities."""
        return self.as_text(localize=False).as_html()
