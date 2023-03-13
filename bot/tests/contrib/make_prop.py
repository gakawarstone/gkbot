from dataclasses import dataclass
from typing import Optional

from contrib.handlers.message.new_context_manager import make_prop


@dataclass
class FakeContext:
    str_data: Optional[str] = None
    integer: Optional[int] = None


def test_make_prop():
    prop = make_prop(FakeContext.str_data, FakeContext)
    assert prop.name == 'str_data'
    assert prop.type == str

    prop = make_prop(FakeContext.integer, FakeContext)
    assert prop.name == 'integer'
    assert prop.type == int
