from dataclasses import dataclass
from typing import Optional, Any

from contrib.handlers.message.context_manager import BaseContextManager, BaseContext
from tests.mocks.message import fake_message


@dataclass
class FakeContext(BaseContext):
    str_data: Optional[str] = None
    integer: Optional[int] = None


class FakeContextManager(BaseContextManager[FakeContext]):
    props = FakeContext
    __user_data = {}

    async def handle(self) -> Any:
        pass

    @property
    def user_data(self) -> dict:
        return self.__user_data


async def test_get_prop():
    ctx_manager = FakeContextManager(event=fake_message)
    assert ctx_manager.ctx.str_data == None


async def test_context_type():
    ctx_manager = FakeContextManager(event=fake_message)
    assert type(ctx_manager.ctx) == FakeContext


async def test_props_type():
    ctx_manager = FakeContextManager(event=fake_message)
    assert ctx_manager.props == FakeContext


async def test_set_cache():
    ctx_manager = FakeContextManager(event=fake_message)
    ctx_manager.set(ctx_manager.props.integer, 10)
    ctx_manager.set(ctx_manager.props.str_data, '10')

    assert ctx_manager.ctx.integer == 10
    assert ctx_manager.ctx.str_data == '10'
    assert ctx_manager.user_data == {
        'str_data': '10',
        'integer': 10
    }


async def test_clean_context():
    ctx_manager = FakeContextManager(event=fake_message)
    ctx_manager.set(ctx_manager.props.integer, 10)
    ctx_manager.set(ctx_manager.props.str_data, '10')
    ctx_manager.clean_context()

    assert ctx_manager.ctx.integer == None
    assert ctx_manager.ctx.str_data == None
    assert ctx_manager.user_data == {
        'str_data': None,
        'integer': None
    }


async def test_clean_context_with_exclude():
    ctx_manager = FakeContextManager(event=fake_message)
    ctx_manager.set(ctx_manager.props.integer, 10)
    ctx_manager.set(ctx_manager.props.str_data, '10')
    ctx_manager.clean_context(ctx_manager.props.integer)

    assert ctx_manager.ctx.integer == 10
    assert ctx_manager.ctx.str_data == None
    assert ctx_manager.user_data == {
        'str_data': None,
        'integer': 10
    }
