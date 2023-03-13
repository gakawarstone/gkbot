from abc import ABC
from typing import Any, Optional, TypeVar, Generic, Type, get_type_hints
from dataclasses import dataclass

from varname import nameof

from .base import BaseHandler as _BaseHandler

_T = TypeVar('_T')


@dataclass
class _Property:
    name: str
    type: type


def uncast_opt(obj: Type) -> Type:
    return obj.__args__[0]


def get_hint(obj_parent: Any, obj_name: str) -> Type:
    return uncast_opt(get_type_hints(obj_parent)[obj_name])


def make_prop(obj: Any, obj_parent: Any, frame=3) -> _Property:
    """Obj must have type hint"""
    obj_name = nameof(obj, frame=frame)  # NOTE: in max frame?
    return _Property(
        name=obj_name,
        type=get_hint(obj_parent, obj_name)
    )


# NOTE: is it required?
class _ContextManagerMixin(Generic[_T]):
    props: _T


class BaseContextManager(_BaseHandler, _ContextManagerMixin[_T], ABC):
    props: Any

    @property
    def ctx(self) -> _T:
        props_name_list: list[str] = [
            prop_name
            for prop_name in dir(self.props)
            if not prop_name.startswith('__')
        ]

        context_args = {}
        for prop_name in props_name_list:
            prop = _Property(prop_name, get_hint(self.props, prop_name))
            context_args[prop_name] = self._try_get_prop(prop)

        return self.props(**context_args)

    def set(self, prop: Any, value: Any) -> None:
        """Example: self.ctx.set(self.props.string, str())"""
        prop = make_prop(prop, self.props)

        if type(value) is not prop.type:
            raise ValueError

        self.user_data[prop.name] = value

    def clean_context(self, *args):
        """Example: self.clean_context(exclude=[self.props.string])"""
        for prop_name in dir(self.props):
            if prop_name.startswith('__'):
                continue

            prop = _Property(prop_name, get_hint(self.props, prop_name))

            exclude = []
            for arg in args:
                exclude.append(make_prop(arg, self.props))

            if prop in exclude:
                continue

            self._reset_prop(prop)

    def _reset_prop(self, prop: _Property) -> None:
        self.user_data[prop.name] = None

    def _try_get_prop(self, prop: _Property) -> Optional[Any]:
        value = self._try_get_from_user_data(prop.name)

        if value is not None and type(value) is not prop.type:
            raise ValueError

        return value
