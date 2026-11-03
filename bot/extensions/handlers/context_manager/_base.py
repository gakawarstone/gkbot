from dataclasses import fields
from enum import StrEnum
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints

from ..base import BaseHandler as _BaseHandler
from ._types import BaseContext


class BaseContextManager[T: BaseContext, K: StrEnum](_BaseHandler):
    props: type[T]
    keys: type[K]

    def _schema(self) -> dict[str, Any]:
        hints = get_type_hints(self.props)
        schema = {field.name: hints[field.name] for field in fields(self.props)}
        for name, hint in schema.items():
            origin = get_origin(hint)
            if origin in (Union, UnionType):
                args = get_args(hint)
                if len(args) != 2 or type(None) not in args:
                    raise TypeError(
                        f"Unsupported annotation for {self.props.__name__}.{name}"
                    )
                hint = next(arg for arg in args if arg is not type(None))
            if (
                hint is Any
                or hint == list[str]
                or (isinstance(hint, type) and hint not in (list, dict, tuple, set))
            ):
                continue
            raise TypeError(f"Unsupported annotation for {self.props.__name__}.{name}")
        return schema

    def _validate(self, name: str, hint: Any, value: Any) -> None:
        origin = get_origin(hint)
        nullable = origin in (Union, UnionType) and type(None) in get_args(hint)
        if nullable:
            hint = next(arg for arg in get_args(hint) if arg is not type(None))
        if hint is Any or (value is None and nullable):
            return
        if hint == list[str]:
            if type(value) is list:
                for index, item in enumerate(value):
                    if type(item) is not str:
                        raise ValueError(
                            f"{self.props.__name__}.{name}[{index}]: expected str, got {type(item).__name__}"
                        )
                return
            expected = "list[str]"
        else:
            if type(value) is hint:
                return
            expected = hint.__name__
        raise ValueError(
            f"{self.props.__name__}.{name}: expected {expected}, got {type(value).__name__}"
        )

    @property
    def ctx(self) -> T:
        schema = self._schema()
        values = {name: self.user_data.get(name) for name in schema}
        for name, value in values.items():
            self._validate(name, schema[name], value)
        return self.props(**values)

    def set(self, prop: K, value: Any) -> None:
        if not isinstance(prop, self.keys):
            raise KeyError(prop)
        schema = self._schema()
        if prop not in schema:
            raise KeyError(prop)
        self._validate(prop, schema[prop], value)
        self.user_data[prop.value] = value

    def clean_context(self, *preserve: K) -> None:
        schema = self._schema()
        for key in preserve:
            if not isinstance(key, self.keys) or key not in schema:
                raise KeyError(key)
        for name in schema:
            if name not in preserve:
                self.user_data[name] = None
