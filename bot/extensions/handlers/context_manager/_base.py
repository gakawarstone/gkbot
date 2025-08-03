from abc import ABC
from typing import TypeVar, Type, Generic, Any, Optional

from ..base import BaseHandler as _BaseHandler
from ._types import Property, BaseContext
from ._utils import get_hint, make_prop, make_args_names_list

_T = TypeVar("_T", bound=BaseContext)


class BaseContextManager(_BaseHandler, Generic[_T], ABC):
    props: Type[_T]

    @property
    def ctx(self) -> _T:
        props_name_list: list[str] = [
            prop_name for prop_name in dir(self.props) if not prop_name.startswith("__")
        ]

        context_args = {}
        for prop_name in props_name_list:
            prop = Property(prop_name, get_hint(self.props, prop_name))
            context_args[prop_name] = self._try_get_prop(prop)

        return self.props(**context_args)

    def set(self, prop: Any, value: Any) -> None:
        """Example: self.ctx.set(self.props.string, str())"""
        prop = make_prop(prop, self.props)

        if type(value) is not prop.type and prop.type is not Any:
            raise ValueError

        self.user_data[prop.name] = value

    def clean_context(self, *args):
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
        self.user_data[prop.name] = None

    def _try_get_prop(self, prop: Property) -> Optional[Any]:
        value = self._try_get_from_user_data(prop.name)

        if value is not None and type(value) is not prop.type and prop.type is not Any:
            raise ValueError

        return value
