from __future__ import annotations

from typing import Any, overload


class ContextField[T]:
    def __init__(self, value_type: Any) -> None:
        self.value_type = value_type
        self.name = ""

    def __set_name__(self, owner: type[BaseContext], name: str) -> None:
        self.name = name

    @overload
    def __get__(
        self, instance: None, owner: type[BaseContext] | None = None
    ) -> ContextField[T]: ...

    @overload
    def __get__(
        self, instance: BaseContext, owner: type[BaseContext] | None = None
    ) -> T | None: ...

    def __get__(
        self, instance: BaseContext | None, owner: type[BaseContext] | None = None
    ) -> Any:
        if instance is None:
            return self
        return instance._values.get(self.name)

    def __set__(self, instance: BaseContext, value: T | None) -> None:
        instance._values[self.name] = value


class BaseContext:
    def __init__(self, **values: Any) -> None:
        self._values = values
