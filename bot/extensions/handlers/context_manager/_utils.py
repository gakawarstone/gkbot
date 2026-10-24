from typing import Any, get_args, get_type_hints

from varname import argname, nameof

from ._types import Property


def uncast_opt(obj: type) -> type:
    return get_args(obj)[0]


def get_hint(obj_parent: Any, obj_name: str) -> type:
    return uncast_opt(get_type_hints(obj_parent)[obj_name])


def make_prop(obj: Any, obj_parent: Any, frame=3) -> Property:
    """Obj must have type hint"""
    obj_name = nameof(obj, frame=frame)  # NOTE: in max frame?
    return Property(name=obj_name, type=get_hint(obj_parent, obj_name))


def make_args_names_list(*args, frame: int = 2) -> list[str]:
    names = []
    for i, _ in enumerate(args):
        arg_id = f"args[{i}]"
        names.append(argname(arg_id, frame=frame))
    return names
