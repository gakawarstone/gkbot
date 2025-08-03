from dataclasses import dataclass
from typing import Optional

from extensions.handlers.context_manager._utils import make_prop


@dataclass
class FakeContext:
    str_data: Optional[str] = None
    integer: Optional[int] = None


def test_make_prop():
    prop = make_prop(FakeContext.str_data, FakeContext, 2)
    assert prop.name == "str_data"
    assert prop.type is str

    prop = make_prop(FakeContext.integer, FakeContext, 2)
    assert prop.name == "integer"
    assert prop.type is int
