from abc import ABC
from typing import Any, Optional
from dataclasses import dataclass

from .base import BaseHandler as _BaseHandler


@dataclass
class Property:
    name: str
    type: type


class BaseContextManager(_BaseHandler, ABC):
    props: Any
    _context_type = type

    @property
    def ctx(self) -> _context_type:
        props_name_list: list[str] = [
            prop_name
            for prop_name in dir(self.props)
            if not prop_name.startswith('__')
        ]

        context_args = {}
        for prop_name in props_name_list:
            context_args[prop_name] = self._try_get_prop(
                getattr(self.props, prop_name))

        return self._context_type(**context_args)

    def set(self, prop: Property, value: Any) -> None:
        if type(value) is not prop.type:
            raise ValueError

        self.user_data[prop.name] = value

    def clean_context(self, exclude: list[Property] = []):
        for prop_name in dir(self.props):
            if prop_name.startswith('__'):
                continue

            prop: Property = getattr(self.props, prop_name)

            if prop in exclude:
                continue

            self._reset_prop(prop)

    def _reset_prop(self, prop: Property) -> None:
        self.user_data[prop.name] = None

    def _try_get_prop(self, prop: Property) -> Optional[Any]:
        value = self._try_get_from_user_data(prop.name)

        if value is not None and type(value) is not prop.type:
            raise ValueError

        return value
