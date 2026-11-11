from datetime import date, time

from .base_creator import BaseCreatorComponent


class RemindCreator(BaseCreatorComponent):
    def __init__(
        self,
        text: str | None = None,
        date: date | None = None,
        time: time | None = None,
        status_message: str | None = None,
    ) -> None:
        self.text = text
        self.date = date
        self.time = time
        self.status_message = status_message
        self._has_highlighted_property = False

        self.date_str = None
        if date:
            self.date_str = date.strftime("%d.%m.%Y")

        self.time_str = None
        if time:
            self.time_str = time.strftime("%H:%M")

    def render(self) -> str:
        text = "<u>Создатель напоминаний ⌚️</u>\n"
        text += self._render_property(self.text, prefix="Текст: ")
        text += self._render_property(self.date_str, prefix="Время: ", new_line=False)
        text += self._render_property(self.time_str)
        text += self._render_if_exist(self.status_message)
        return text
