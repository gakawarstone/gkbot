from collections.abc import Iterator
from unittest.mock import AsyncMock, patch

import pytest
from aiogram import Bot, Dispatcher, Router
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.dispatcher.event.handler import FilterObject
from aiogram.filters import Command
from aiogram.filters.logic import _AndFilter, _OrFilter
from aiogram.types import Message, Update

from bot import handlers, modules
from configs.commands import USER_COMMANDS
from configs.default_commands import DEFAULT_COMMANDS
from core.commands import Commands
from core.default_commands import DefaultCommands
from filters.command import CommandWithPrompt
from tests.mocks.message import make_fake_message


@pytest.fixture
def dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    handlers.setup(dispatcher)
    modules.setup(dispatcher)
    return dispatcher


def _filter_commands(filter_object: FilterObject) -> Iterator[Commands]:
    callback = filter_object.callback
    if isinstance(callback, Command):
        for command in callback.commands:
            assert isinstance(command, USER_COMMANDS), (
                f"Command registration bypasses the shared registry: {command!r}"
            )
            yield command
    elif isinstance(callback, CommandWithPrompt):
        assert isinstance(callback.command, USER_COMMANDS)
        yield callback.command
    elif isinstance(callback, (_AndFilter, _OrFilter)):
        # aiogram wraps commands combined with chat or FSM filters in targets.
        for target in callback.targets:
            yield from _filter_commands(target)


def _registered_commands(router: Router) -> list[Commands]:
    return [
        command
        for child in router.chain_tail
        for handler in child.message.handlers
        for filter_object in handler.filters or []
        for command in _filter_commands(filter_object)
    ]


def test_registered_commands_match_registry_and_defaults(
    dispatcher: Dispatcher,
) -> None:
    registered = _registered_commands(dispatcher)
    names = [command.value for command in registered]

    assert len(names) == len(set(names)), "Duplicate command registrations"
    assert set(names) == set(USER_COMMANDS.as_list()) == set(DEFAULT_COMMANDS)
    assert {"admins", "set_tz", "img", "wait", "feed", "add_feed", "login_feed"} <= set(
        names
    )


async def test_telegram_defaults_match_registered_commands(
    dispatcher: Dispatcher,
) -> None:
    bot = AsyncMock(spec=Bot)

    await DefaultCommands(DEFAULT_COMMANDS).set(bot)

    bot.set_my_commands.assert_awaited_once()
    commands = bot.set_my_commands.await_args.args[0]
    advertised = {command.command: command.description for command in commands}
    assert len(commands) == len(advertised)
    assert advertised == {
        command.value: command.description
        for command in _registered_commands(dispatcher)
    }


async def test_list_contains_exactly_registered_commands(
    dispatcher: Dispatcher,
) -> None:
    update = Update(update_id=1, message=make_fake_message("/list"))

    async with Bot(token="12345678:ABCDEF-GHIJKLMNOPQRSTUV") as bot:
        with patch.object(Message, "answer", new_callable=AsyncMock) as answer:
            await dispatcher.feed_update(bot, update)

    answer.assert_awaited_once()
    assert answer.await_args is not None
    text = answer.await_args.args[0]
    names = [
        line.removeprefix("/") for line in text.splitlines() if line.startswith("/")
    ]
    assert len(names) == len(set(names))
    assert names == sorted(
        command.value for command in _registered_commands(dispatcher)
    )


@pytest.mark.parametrize("command", ["start", "sub"])
async def test_commands_without_handlers_are_not_advertised(
    dispatcher: Dispatcher, command: str
) -> None:
    update = Update(update_id=1, message=make_fake_message(f"/{command}"))

    async with Bot(token="12345678:ABCDEF-GHIJKLMNOPQRSTUV") as bot:
        with patch.object(Message, "answer", new_callable=AsyncMock) as answer:
            result = await dispatcher.feed_update(bot, update)

    assert result is UNHANDLED
    answer.assert_not_awaited()
    assert command not in USER_COMMANDS.as_list()
    assert command not in DEFAULT_COMMANDS
