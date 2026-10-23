"""Callbacks are validated before any download handler is entered."""

from importlib import import_module

import pytest
from aiogram import Router
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery

from tests.mocks.message import make_fake_callback
from ui.buttons.matreshka import MatreshkaDownloadButtonCallbackData
from ui.buttons.pornhub.download import PornhubDownloadButtonCallbackData
from ui.buttons.porno365 import Porno365DownloadButtonCallbackData
from ui.buttons.sasflix import SasflixDownloadButtonCallbackData
from ui.buttons.vk import VKDownloadButtonCallbackData
from ui.buttons.youtube.download import YoutubeDownloadButtonCallbackData

ROUTES = [
    (
        "youtube",
        YoutubeDownloadButtonCallbackData,
        "ytbtn:dlmp4:0:000opaque",
        "ytbtn:dlmp4:False:000opaque",
    ),
    (
        "vk",
        VKDownloadButtonCallbackData,
        "vk2|dlmp4|0|short_url|https://vk.cc/abc",
        "vkbtn:dlmp4:False:https://vk.cc/abc",
    ),
    (
        "pornhub",
        PornhubDownloadButtonCallbackData,
        "phbtn:dlmp4:0:ph0001",
        "phbtn:dlmp4:False:ph0001",
    ),
    (
        "porno365",
        Porno365DownloadButtonCallbackData,
        "p365v2|dlmp4|0|https://porno365.example/v/1",
        "p365btn:dlmp4:False:https://porno365.example/v/1",
    ),
    (
        "matreshka",
        MatreshkaDownloadButtonCallbackData,
        "matreshkabtn:000opaque",
        "matreshkabtn:000opaque",
    ),
    (
        "sasflix",
        SasflixDownloadButtonCallbackData,
        "sasflixbtn:12345678123456781234567812345678",
        "sasflixbtn:12345678-1234-5678-1234-567812345678",
    ),
]


@pytest.mark.parametrize("source, model, native, legacy", ROUTES)
@pytest.mark.parametrize("wire_format", ["native", "legacy"])
async def test_typed_payload_injection(
    monkeypatch: pytest.MonkeyPatch,
    source: str,
    model: type[CallbackData],
    native: str,
    legacy: str,
    wire_format: str,
) -> None:
    async def capture(
        query: CallbackQuery, callback_data: CallbackData
    ) -> CallbackData:
        return callback_data

    handler = import_module(f"handlers.button.{source}.download")
    monkeypatch.setattr(handler, "download", capture)
    router = Router()
    handler.setup(router)
    raw = native if wire_format == "native" else legacy
    result = await router.propagate_event("callback_query", make_fake_callback(raw))
    assert isinstance(result, model)
    assert result == model.unpack(native)


@pytest.mark.parametrize("source, model, native, legacy", ROUTES)
@pytest.mark.parametrize("damage", ["prefix", "extra", "missing", "empty", "no-data"])
async def test_malformed_callback_never_enters_handler(
    monkeypatch: pytest.MonkeyPatch,
    source: str,
    model: type[CallbackData],
    native: str,
    legacy: str,
    damage: str,
) -> None:
    async def forbidden(query: CallbackQuery, callback_data: CallbackData) -> None:
        pytest.fail("Invalid callback entered the download handler")

    handler = import_module(f"handlers.button.{source}.download")
    monkeypatch.setattr(handler, "download", forbidden)
    router = Router()
    handler.setup(router)
    sep = model.__separator__
    parts = native.split(sep)
    if damage == "prefix":
        parts[0] += "lookalike"
    elif damage == "extra":
        parts.append("extra")
    elif damage == "missing":
        parts.pop()
    else:
        parts[-1] = ""
    callback = make_fake_callback(sep.join(parts))
    if damage == "no-data":
        callback = callback.model_copy(update={"data": None})
    assert await router.propagate_event("callback_query", callback) is UNHANDLED


@pytest.mark.parametrize("source, model, native, legacy", ROUTES[:4])
@pytest.mark.parametrize("wire_format", ["native", "legacy"])
@pytest.mark.parametrize("token", ["", "yes", "on", "false", "garbage", "2"])
async def test_invalid_boolean_never_enters_handler(
    monkeypatch: pytest.MonkeyPatch,
    source: str,
    model: type[CallbackData],
    native: str,
    legacy: str,
    wire_format: str,
    token: str,
) -> None:
    async def forbidden(query: CallbackQuery, callback_data: CallbackData) -> None:
        pytest.fail("Malformed boolean entered the download handler")

    handler = import_module(f"handlers.button.{source}.download")
    monkeypatch.setattr(handler, "download", forbidden)
    router = Router()
    handler.setup(router)
    raw = native if wire_format == "native" else legacy
    sep = model.__separator__ if wire_format == "native" else ":"
    parts = raw.split(sep, 3)
    parts[2] = token
    assert (
        await router.propagate_event(
            "callback_query", make_fake_callback(sep.join(parts))
        )
        is UNHANDLED
    )


@pytest.mark.parametrize("source, model, native, legacy", ROUTES[:4])
@pytest.mark.parametrize("wire_format", ["native", "legacy"])
async def test_unknown_action_never_enters_handler(
    monkeypatch: pytest.MonkeyPatch,
    source: str,
    model: type[CallbackData],
    native: str,
    legacy: str,
    wire_format: str,
) -> None:
    async def forbidden(query: CallbackQuery, callback_data: CallbackData) -> None:
        pytest.fail("Unknown action entered the download handler")

    handler = import_module(f"handlers.button.{source}.download")
    monkeypatch.setattr(handler, "download", forbidden)
    router = Router()
    handler.setup(router)
    raw = native if wire_format == "native" else legacy
    sep = model.__separator__ if wire_format == "native" else ":"
    parts = raw.split(sep, 3)
    parts[1] = "unknown"
    assert (
        await router.propagate_event(
            "callback_query", make_fake_callback(sep.join(parts))
        )
        is UNHANDLED
    )
