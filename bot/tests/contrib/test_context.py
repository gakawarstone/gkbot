from dataclasses import dataclass
from typing import Any

import pytest

from extensions.handlers.context_manager import BaseContext, BaseContextManager
from tests.mocks.message import fake_event


@dataclass
class FakeContext(BaseContext):
    str_data: str | None = None
    integer: int | None = None
    any: Any = None
    messages: list[str] | None = None

    def method(self) -> None:
        pass


class FakeContextManager(BaseContextManager[FakeContext]):
    props = FakeContext

    def __init__(self) -> None:
        super().__init__(event=fake_event)
        self._user_data: dict[str, Any] = {}

    async def handle(self) -> None:
        pass

    @property
    def user_data(self) -> dict[str, Any]:
        return self._user_data


def test_context_read_write_and_identity() -> None:
    manager = FakeContextManager()
    assert manager.ctx.str_data is None
    history = ["hello"]
    manager.set("integer", 10)
    manager.set("str_data", "10")
    manager.set("any", object())
    manager.set("messages", history)
    assert manager.ctx.integer == 10
    assert manager.ctx.str_data == "10"
    assert manager.ctx.messages is history
    assert "method" not in manager.user_data


def test_cleanup_preserves_fields_and_unrelated_data() -> None:
    manager = FakeContextManager()
    manager.user_data.update(integer=10, str_data="text", any="keep", delete_queue=[1])
    manager.clean_context("integer", "any")
    assert manager.user_data == {
        "integer": 10,
        "str_data": None,
        "any": "keep",
        "messages": None,
        "delete_queue": [1],
    }


def test_unknown_keys_do_not_partially_mutate() -> None:
    manager = FakeContextManager()
    manager.user_data.update(integer=10, str_data="text")
    before = manager.user_data.copy()
    with pytest.raises(KeyError):
        manager.clean_context("integer", "unknown")
    with pytest.raises(KeyError):
        manager.set("method", 1)
    assert manager.user_data == before


def test_parameterized_list_validation_on_read_and_write() -> None:
    manager = FakeContextManager()
    manager.set("messages", [])
    manager.set("messages", ["one", "two"])
    with pytest.raises(ValueError, match=r"FakeContext.messages\[1\]"):
        manager.set("messages", ["one", 2])
    assert manager.ctx.messages == ["one", "two"]
    manager.user_data["messages"].append(2)
    with pytest.raises(ValueError, match=r"FakeContext.messages\[2\]"):
        _ = manager.ctx
    manager.clean_context()
    assert manager.ctx.messages is None


def test_validation_handles_optional_any_and_exact_types() -> None:
    manager = FakeContextManager()
    manager.set("integer", None)
    manager.set("any", None)
    with pytest.raises(ValueError, match="expected int, got bool"):
        manager.set("integer", True)
    with pytest.raises(ValueError, match="expected list"):
        manager.set("messages", "not a list")
    assert manager.user_data == {"integer": None, "any": None}


def test_unsupported_annotation_fails_before_mutation() -> None:
    @dataclass
    class UnsupportedContext(BaseContext):
        value: dict[str, str] | None = None

    class UnsupportedManager(FakeContextManager):
        props = UnsupportedContext

    manager = UnsupportedManager()
    manager.user_data["unrelated"] = 1
    with pytest.raises(TypeError, match="Unsupported annotation"):
        manager.clean_context()
    assert manager.user_data == {"unrelated": 1}


def test_all_production_contexts_read_legacy_data() -> None:
    from datetime import date, time, timedelta

    from aiogram.types import Message

    from handlers.user.books.messages.add._context import _AddBookContext
    from handlers.user.books.messages.edit_property._context import (
        _EditBookPropertyContext,
    )
    from handlers.user.chatgpt._context import _ChatGPTContext
    from handlers.user.download._context import _DownloadContext
    from handlers.user.reminder._context import _ReminderContext
    from handlers.user.road.settings._context import RoadSettingsContext

    class LegacyManager(BaseContextManager[BaseContext]):
        def __init__(self, schema: type[BaseContext], data: dict[str, Any]) -> None:
            super().__init__(event=fake_event)
            self.props = schema
            self._data = data

        @property
        def user_data(self) -> dict[str, Any]:
            return self._data

        async def handle(self) -> None:
            pass

    message = Message.model_construct(message_id=1)
    history = ["hello"]
    cases: list[tuple[type[BaseContext], dict[str, Any]]] = [
        (_ChatGPTContext, {"messages": history}),
        (_DownloadContext, {"file_name": "file"}),
        (
            _ReminderContext,
            {
                "text": "hello",
                "tz": timedelta(hours=1),
                "date": date(2026, 1, 1),
                "time": time(12),
                "message": message,
            },
        ),
        (RoadSettingsContext, {"setting_name": "time", "setting_new_value": time(12)}),
        (
            _AddBookContext,
            {"name": "book", "author": "author", "chapter_cnt": 2, "message": message},
        ),
        (
            _EditBookPropertyContext,
            {"property_name": "name", "new_value": "new", "book_id": 1},
        ),
    ]
    for schema, values in cases:
        data = {**values, "unrelated": object()}
        manager = LegacyManager(schema, data)
        view = manager.ctx
        for key, value in values.items():
            assert getattr(view, key) is value
        preserved_key = next(iter(values))
        manager.clean_context(preserved_key)
        assert data[preserved_key] is values[preserved_key]
        assert "unrelated" in data
        for key in values.keys() - {preserved_key}:
            assert data[key] is None
