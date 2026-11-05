from collections.abc import MutableMapping
from typing import Any, cast

from ..base import BaseHandler as _BaseHandler
from ._types import BaseContext, ContextField


class BaseContextManager[T: BaseContext](_BaseHandler):
    props: type[T]

    @property
    def _context_values(self) -> MutableMapping[str, Any]:
        # ContextField names are dynamic and validated against the context schema.
        return cast(MutableMapping[str, Any], self.user_data)

    def _schema(self) -> dict[str, ContextField[Any]]:
        schema: dict[str, ContextField[Any]] = {}
        for cls in reversed(self.props.__mro__):
            for name, value in vars(cls).items():
                if isinstance(value, ContextField):
                    schema[name] = value
        for name, field in schema.items():
            hint = field.value_type
            if (
                hint is Any
                or hint == list[str]
                or (isinstance(hint, type) and hint not in (list, dict, tuple, set))
            ):
                continue
            raise TypeError(f"Unsupported annotation for {self.props.__name__}.{name}")
        return schema

    def _validate(self, field: ContextField[Any], value: Any) -> None:
        hint = field.value_type
        if hint is Any or value is None:
            return
        if hint == list[str]:
            if type(value) is list:
                for index, item in enumerate(value):
                    if type(item) is not str:
                        raise ValueError(
                            f"{self.props.__name__}.{field.name}[{index}]: expected str, got {type(item).__name__}"
                        )
                return
            expected = "list[str]"
        else:
            if type(value) is hint:
                return
            expected = hint.__name__
        raise ValueError(
            f"{self.props.__name__}.{field.name}: expected {expected}, got {type(value).__name__}"
        )

    @property
    def ctx(self) -> T:
        schema = self._schema()
        values = {name: self.user_data.get(name) for name in schema}
        for name, value in values.items():
            self._validate(schema[name], value)
        return self.props(**values)

    def set[V](self, prop: ContextField[V], value: V | None) -> None:
        schema = self._schema()
        if not isinstance(prop, ContextField) or schema.get(prop.name) is not prop:
            raise KeyError(prop)
        self._validate(prop, value)
        self._context_values[prop.name] = value

    def clean_context(self, *preserve: ContextField[Any]) -> None:
        schema = self._schema()
        for field in preserve:
            if (
                not isinstance(field, ContextField)
                or schema.get(field.name) is not field
            ):
                raise KeyError(field)
        preserved = {field.name for field in preserve}
        for name in schema:
            if name not in preserved:
                self._context_values[name] = None
