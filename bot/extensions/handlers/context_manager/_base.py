from collections.abc import MutableMapping
from typing import Any, cast

from ..base import BaseHandler as _BaseHandler
from ._types import BaseContext, Property
from ._utils import get_hint, make_args_names_list, make_prop


class BaseContextManager[T: BaseContext](_BaseHandler):
    props: type[T]

    @property
    def ctx(self) -> T:
        props_name_list: list[str] = [
            prop_name for prop_name in dir(self.props) if not prop_name.startswith("__")
        ]

        context_args = {}
        for prop_name in props_name_list:
            prop = Property(prop_name, get_hint(self.props, prop_name))
            context_args[prop_name] = self._try_get_prop(prop)

        return self.props(**context_args)

    @property
    def _context_values(self) -> MutableMapping[str, Any]:
        # The legacy context manager validates dynamic dataclass fields at runtime.
        # Keep its writes separate from statically checked middleware keys.
        return cast(MutableMapping[str, Any], self.user_data)

    def set(self, prop: Any, value: Any) -> None:
        """Example: self.ctx.set(self.props.string, str())"""
        prop = make_prop(prop, self.props)

        if type(value) is not prop.type and prop.type is not Any:
            raise ValueError

        self._context_values[prop.name] = value

    def clean_context(self, *args: Any) -> None:
        """
        Example: self.clean_context(self.props.string)
        where self.props.string not cleaning
        """
        for prop_name in dir(self.props):
            if prop_name.startswith("__"):
                continue

            exclude = make_args_names_list(*args)
            if prop_name in exclude:
                continue

            prop = Property(prop_name, get_hint(self.props, prop_name))

            self._reset_prop(prop)

    def _reset_prop(self, prop: Property) -> None:
        self._context_values[prop.name] = None

    def _try_get_prop(self, prop: Property) -> Any | None:
        value = self._try_get_from_user_data(prop.name)

        if value is not None and type(value) is not prop.type and prop.type is not Any:
            raise ValueError

        return value
