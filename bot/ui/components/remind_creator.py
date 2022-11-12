from typing import Optional, Any
from datetime import date, time

from .base import BaseComponent


class RemindCreator(BaseComponent):
    def __init__(
        self,
        text: Optional[str] = None,
        date: Optional[date] = None,
        time: Optional[time] = None,
        status_message: Optional[str] = None
    ) -> None:
        self.text = text
        self.date = date
        self.time = time
        self.status_message = status_message
        self.__has_highlighted_property = False

        if date:
            self.date = date.strftime('%d.%m.%Y')

        if time:
            self.time = time.strftime('%H:%M')

    def render(self) -> str:
        text = '<u>Создатель напоминаний ⌚️</u>\n'
        text += self.__render_property(self.text, prefix='Текст: ')
        text += self.__render_property(self.date,
                                       prefix='Время: ', new_line=False)
        text += self.__render_property(self.time)
        text += self._render_if_exist(self.status_message)
        return text

    def __render_property(self, prop: Any, prefix: str = '',
                          new_line: bool = True) -> str:
        highlight = self._is_property_not_exist(prop) \
            and not self.__has_highlighted_property
        text = self._highlight_if(
            highlight, prefix + self._render_if_exist(prop, '... '))
        if new_line:
            text += '\n'

        if highlight:
            self.__has_highlighted_property = True

        return text
