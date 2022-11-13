from datetime import date, time, timedelta
from dataclasses import dataclass
from typing import Optional, Any

from aiogram.types import Message

from contrib.handlers.message.base import BaseHandler as _BaseHandler


@dataclass
class _Property:
    name: str
    type: type


class _Properties:
    text = _Property('text', str)
    tz = _Property('tz', timedelta)
    date = _Property('date', date)
    time = _Property('time', time)
    message = _Property('mes', Message)


@dataclass
class _ReminderContext:
    text: Optional[_Properties.text.type]
    tz: Optional[_Properties.tz.type]
    date: Optional[_Properties.date.type]
    time: Optional[_Properties.time.type]
    message: Optional[_Properties.message.type]


class ReminderContextManager(_BaseHandler):
    props = _Properties

    @property
    def ctx(self) -> _ReminderContext:
        return _ReminderContext(
            text=self._try_get_prop(self.props.text),
            tz=self._try_get_prop(self.props.tz),
            date=self._try_get_prop(self.props.date),
            time=self._try_get_prop(self.props.time),
            message=self._try_get_prop(self.props.message)
        )

    def set(self, prop: _Property, value: Any) -> None:
        if type(value) is not prop.type:
            raise ValueError

        self.user_data[prop.name] = value

    def clean_context(self, exclude: list[_Property] = []):
        for prop_name in dir(self.props):
            if prop_name.startswith('__'):
                continue

            if prop_name in [p.name for p in exclude]:
                continue

            prop = getattr(self.props, prop_name)
            self._reset_prop(prop)

    def _reset_prop(self, prop: _Property) -> None:
        self.user_data[prop.name] = None

    def _try_get_prop(self, prop: _Property) -> Optional[Any]:
        value = self._try_get_from_user_data(prop.name)

        if value is not None and type(value) is not prop.type:
            raise ValueError

        return value
