from typing import Optional
from datetime import date, time

from .base import BaseComponent


class RemindCreator(BaseComponent):
    def __init__(
        self,
        text: Optional[str] = None,
        date: Optional[date] = None,
        time: Optional[time] = None,
        status_message: Optional[str] = None,
    ) -> None:
        self.text = text
        self.date = date
        self.time = time
        self.status_message = status_message
        self._has_highlighted_property = False

        if date:
            self.date = date.strftime("%d.%m.%Y")

        if time:
            self.time = time.strftime("%H:%M")

    def render(self) -> str:
        text = "<u>Создатель напоминаний ⌚️</u>\n"
        text += self._render_property(self.text, prefix="Текст: ")
        text += self._render_property(self.date, prefix="Время: ", new_line=False)
        text += self._render_property(self.time)
        text += self._render_if_exist(self.status_message)
        return text
