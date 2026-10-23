import asyncio
import gzip
import json
import shutil
import socket
import subprocess
import threading
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import aiohttp
import pytest
import pytest_asyncio
from aiohttp import web

import core.bot as bot_module
from core.types import BotConfig
from services.cache_dir import CacheDir
from services.http import HttpRequestError, HttpService, ResponseTooLargeError

METHODS = [
    "get",
    "get_json",
    "post",
    "post_json",
    "get_redirected_url",
    "extract_cookies",
]
BODY_METHODS = ["get", "get_json", "post", "post_json"]


async def call(method: str, url: str) -> Any:
    if method in ("post", "post_json"):
        return await getattr(HttpService, method)(url, {"hello": "world"})
    return await getattr(HttpService, method)(url)


@pytest_asyncio.fixture(loop_scope="function", autouse=True)
async def session_cleanup() -> AsyncIterator[None]:
    yield
    await HttpService.close()


@pytest_asyncio.fixture(loop_scope="function")
async def server() -> AsyncIterator[str]:
    async def handle(request: web.Request) -> web.StreamResponse:
        kind = request.match_info["kind"]
        if kind in ("404", "503"):
            return web.Response(status=int(kind), body=b"invalid json")
        if kind == "redirect":
            raise web.HTTPFound("/success")
        if kind == "loop":
            raise web.HTTPFound("/loop")
        if kind == "slow":
            await asyncio.sleep(0.1)
        if kind == "invalid":
            return web.Response(body=b"{", content_type="application/json")
        if kind == "unicode":
            return web.Response(body=b'"\xff"', content_type="application/json")
        if kind == "charset":
            return web.Response(
                body=b"{}",
                headers={"Content-Type": "application/json; charset=unknown"},
            )
        if kind == "integer":
            return web.Response(body=b"1" * 5000, content_type="application/json")
        if kind == "content_type":
            return web.Response(text="{}")
        if kind == "suffix":
            return web.Response(body=b"{}", content_type="application/problem+json")
        if kind in ("large", "compressed", "chunked"):
            body = b'"' + b"x" * 64 + b'"'
            if kind == "compressed":
                return web.Response(
                    body=gzip.compress(body),
                    content_type="application/json",
                    headers={"Content-Encoding": "gzip"},
                )
            if kind == "chunked":
                response = web.StreamResponse(
                    headers={"Content-Type": "application/json"}
                )
                await response.prepare(request)
                await response.write(body[:32])
                await response.write(body[32:])
                await response.write_eof()
                return response
            return web.Response(body=body, content_type="application/json")
        if kind in ("stalled", "truncated"):
            response = web.StreamResponse(
                headers={"Content-Type": "application/json", "Content-Length": "100"}
            )
            await response.prepare(request)
            if kind == "stalled":
                await asyncio.sleep(0.1)
            else:
                assert request.transport is not None
                request.transport.close()
            return response
        if kind == "echo":
            if request.content_type == "application/json":
                return web.json_response(await request.json())
            return web.json_response(dict(await request.post()))
        if kind == "cookies":
            return web.Response(text=request.headers.get("Cookie", ""))
        response = web.json_response({"hello": "world"})
        response.set_cookie("token", "value")
        return response

    app = web.Application()
    app.router.add_route("*", "/{kind}", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    try:
        yield f"http://127.0.0.1:{runner.addresses[0][1]}"
    finally:
        await runner.cleanup()


@pytest.mark.parametrize("method", METHODS)
async def test_success_and_redirects(server: str, method: str) -> None:
    result = await call(method, server + "/success")
    if method in ("get", "post"):
        assert json.loads(result) == {"hello": "world"}
    elif method in ("get_json", "post_json"):
        assert result == {"hello": "world"}
    elif method == "extract_cookies":
        assert result["token"].value == "value"
    else:
        assert result == server + "/success"
    # aiohttp follows POST redirects with a GET, preserving the previous behavior.
    redirected = await call(method, server + "/redirect")
    assert redirected == result


@pytest.mark.parametrize("method", ["post", "post_json"])
async def test_post_payload(server: str, method: str) -> None:
    result = await call(method, server + "/echo")
    assert (json.loads(result) if isinstance(result, bytes) else result) == {
        "hello": "world"
    }


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("status", [404, 503])
async def test_status_before_decoding(server: str, method: str, status: int) -> None:
    with pytest.raises(HttpRequestError) as raised:
        await call(method, server + f"/{status}")
    cause = raised.value.__cause__
    assert isinstance(cause, aiohttp.ClientResponseError)
    assert cause.status == status


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("endpoint", ["slow", "loop"])
async def test_timeout_and_redirect_loop(
    server: str, monkeypatch: pytest.MonkeyPatch, method: str, endpoint: str
) -> None:
    monkeypatch.setattr(
        HttpService,
        "timeout",
        aiohttp.ClientTimeout(
            total=0.05, connect=0.05, sock_connect=0.05, sock_read=0.05
        ),
    )
    with pytest.raises(HttpRequestError) as raised:
        await call(method, server + "/" + endpoint)
    expected = TimeoutError if endpoint == "slow" else aiohttp.TooManyRedirects
    assert isinstance(raised.value.__cause__, expected)


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize(
    "failure", ["invalid_url", "invalid_host", "invalid_port", "connection"]
)
async def test_connection_errors(method: str, failure: str) -> None:
    expected: type[Exception]
    if failure == "invalid_url":
        url = "http://"
        expected = aiohttp.InvalidURL
    elif failure == "invalid_host":
        url = "http://["
        expected = ValueError
    elif failure == "invalid_port":
        url = "http://127.0.0.1:invalid"
        expected = ValueError
    else:
        # Reserve a local port without listening, so refusal does not use DNS.
        with socket.socket() as reserved:
            reserved.bind(("127.0.0.1", 0))
            url = f"http://127.0.0.1:{reserved.getsockname()[1]}"
            with pytest.raises(HttpRequestError) as raised:
                await call(method, url)
        assert isinstance(raised.value.__cause__, aiohttp.ClientConnectorError)
        return
    with pytest.raises(HttpRequestError) as raised:
        await call(method, url)
    assert isinstance(raised.value.__cause__, expected)


@pytest.mark.parametrize("method", ["get_json", "post_json"])
@pytest.mark.parametrize(
    ("endpoint", "cause"),
    [
        ("invalid", json.JSONDecodeError),
        ("unicode", UnicodeDecodeError),
        ("charset", LookupError),
        ("integer", ValueError),
        ("content_type", aiohttp.ContentTypeError),
    ],
)
async def test_json_failures(
    server: str, method: str, endpoint: str, cause: type[Exception]
) -> None:
    with pytest.raises(HttpRequestError) as raised:
        await call(method, server + "/" + endpoint)
    assert isinstance(raised.value.__cause__, cause)


@pytest.mark.parametrize("method", ["get_json", "post_json"])
async def test_json_recursion_failure(
    server: str, monkeypatch: pytest.MonkeyPatch, method: str
) -> None:
    # Decoder recursion limits differ between Python versions.
    error = RecursionError("JSON nesting exceeds the decoder limit")
    monkeypatch.setattr(json, "loads", Mock(side_effect=error))
    with pytest.raises(HttpRequestError) as raised:
        await call(method, server + "/success")
    assert raised.value.__cause__ is error


@pytest.mark.parametrize("method", ["get_json", "post_json"])
async def test_json_content_type_suffix(server: str, method: str) -> None:
    assert await call(method, server + "/suffix") == {}


@pytest.mark.parametrize("method", BODY_METHODS)
@pytest.mark.parametrize("endpoint", ["large", "compressed", "chunked"])
async def test_size_limit(
    server: str, monkeypatch: pytest.MonkeyPatch, method: str, endpoint: str
) -> None:
    monkeypatch.setattr(HttpService, "max_body_bytes", 65)
    monkeypatch.setattr(HttpService, "max_json_bytes", 65)
    with pytest.raises(HttpRequestError) as raised:
        await call(method, server + "/" + endpoint)
    assert isinstance(raised.value.__cause__, ResponseTooLargeError)


@pytest.mark.parametrize("method", BODY_METHODS)
async def test_exact_size_limit(
    server: str, monkeypatch: pytest.MonkeyPatch, method: str
) -> None:
    monkeypatch.setattr(HttpService, "max_body_bytes", 66)
    monkeypatch.setattr(HttpService, "max_json_bytes", 66)
    assert await call(method, server + "/large")


@pytest.mark.parametrize("method", BODY_METHODS)
@pytest.mark.parametrize("endpoint", ["stalled", "truncated"])
async def test_body_transport_failures(
    server: str, monkeypatch: pytest.MonkeyPatch, method: str, endpoint: str
) -> None:
    monkeypatch.setattr(
        HttpService, "timeout", aiohttp.ClientTimeout(total=0.05, sock_read=0.03)
    )
    with pytest.raises(HttpRequestError) as raised:
        await call(method, server + "/" + endpoint)
    expected = TimeoutError if endpoint == "stalled" else aiohttp.ClientPayloadError
    assert isinstance(raised.value.__cause__, expected)


async def test_reuse_cookies_and_close(server: str) -> None:
    await asyncio.gather(*(HttpService.get(server + "/success") for _ in range(4)))
    session = HttpService._session
    assert session is not None
    assert session.timeout.total == 120
    assert session.timeout.connect == session.timeout.sock_connect == 10
    assert session.timeout.sock_read == 30
    assert await HttpService.get(server + "/cookies") == b""
    assert HttpService._session is session
    await HttpService.close()
    await HttpService.close()
    assert session.closed
    await HttpService.get(server + "/success")
    assert HttpService._session is not session


async def test_cancellation_propagates(server: str) -> None:
    task = asyncio.create_task(HttpService.get(server + "/slow"))
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert await HttpService.get_json(server + "/success") == {"hello": "world"}


@pytest.fixture
def cache_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(CacheDir, "_CacheDir__base_path", str(tmp_path))
    return tmp_path


@pytest.mark.parametrize(
    "method", ["get_with_downloader", "download_file_to_path", "download_file"]
)
@pytest.mark.parametrize("failure", [None, "status", "timeout", "missing"])
async def test_downloader_failures_and_ownership(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch, method: str, failure: str | None
) -> None:
    errors = {
        "status": subprocess.CalledProcessError(22, "aria2c"),
        "timeout": subprocess.TimeoutExpired("aria2c", 120),
        "missing": FileNotFoundError("aria2c"),
    }

    def run(command: list[str], **kwargs: Any) -> None:
        assert kwargs["check"] is True
        assert kwargs["timeout"] == 120
        assert "--connect-timeout=10" in command
        assert "--timeout=30" in command
        assert "--max-tries=1" in command
        path = (
            Path(command[command.index("--dir") + 1])
            / command[command.index("--out") + 1]
        )
        path.write_bytes(b"response")
        if failure is not None:
            raise errors[failure]

    monkeypatch.setattr(subprocess, "run", run)
    output = cache_root / "caller-owned"

    async def download() -> None:
        if method == "download_file":
            async with HttpService.download_file("https://example.invalid") as path:
                assert Path(path).read_bytes() == b"response"
        elif method == "download_file_to_path":
            await HttpService.download_file_to_path(
                "https://example.invalid", str(output)
            )
        else:
            assert (
                await HttpService.get_with_downloader("https://example.invalid")
                == b"response"
            )

    if failure is not None:
        with pytest.raises(HttpRequestError) as raised:
            await download()
        assert raised.value.__cause__ is errors[failure]
    else:
        await download()
    assert list(cache_root.iterdir()) == (
        [output] if method == "download_file_to_path" else []
    )


async def test_downloader_bounded_read(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def download(url: str, path: str, headers: dict[str, str] | None) -> None:
        assert headers == {"User-Agent": "test"}
        Path(path).write_bytes(b"12345")

    monkeypatch.setattr(HttpService, "_download", download)
    monkeypatch.setattr(HttpService, "max_body_bytes", 4)
    with pytest.raises(HttpRequestError) as raised:
        await HttpService.get_with_downloader(
            "https://example.invalid", {"User-Agent": "test"}
        )
    assert isinstance(raised.value.__cause__, ResponseTooLargeError)
    assert list(cache_root.iterdir()) == []


async def test_downloader_cancel_waits_for_worker(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    started = threading.Event()
    release = threading.Event()

    def run(command: list[str], **kwargs: Any) -> None:
        directory = Path(command[command.index("--dir") + 1])
        started.set()
        assert release.wait(5)
        assert directory.is_dir()
        (directory / "response").write_bytes(b"done")

    monkeypatch.setattr(subprocess, "run", run)
    task = asyncio.create_task(
        HttpService.get_with_downloader("https://example.invalid")
    )
    try:
        assert await asyncio.to_thread(started.wait, 5)
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        assert list(cache_root.iterdir())
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert list(cache_root.iterdir()) == []


@pytest.mark.parametrize("failure", [None, "startup", "polling", "cancel"])
def test_bot_closes_http_session(
    monkeypatch: pytest.MonkeyPatch, failure: str | None
) -> None:
    sessions: list[aiohttp.ClientSession] = []
    error = asyncio.CancelledError() if failure == "cancel" else RuntimeError("failed")

    async def hook() -> None:
        sessions.append(HttpService._get_session())
        if failure == "startup":
            raise error

    starter = bot_module.BotStarter(
        BotConfig(
            token="12345678:ABCDEF-GHIJKLMNOPQRSTUV",
            startup_hooks=[hook],
            default_commands={},
            parse_mode="HTML",
            admins=[],
        )
    )
    monkeypatch.setattr(bot_module.Notifier, "setup", AsyncMock())
    monkeypatch.setattr(bot_module.DefaultCommands, "set", AsyncMock())
    for module in (bot_module.middlewares, bot_module.handlers, bot_module.modules):
        monkeypatch.setattr(module, "setup", Mock())
    polling = AsyncMock(side_effect=error if failure in ("polling", "cancel") else None)
    monkeypatch.setattr(starter.dp, "start_polling", polling)
    if failure is None:
        starter.start()
    else:
        with pytest.raises(type(error)) as raised:
            starter.start()
        assert raised.value is error
    assert len(sessions) == 1 and sessions[0].closed
    assert HttpService._session is None
    assert polling.await_count == (0 if failure == "startup" else 1)


@pytest.mark.skipif(shutil.which("aria2c") is None, reason="aria2c is not installed")
@pytest.mark.parametrize(
    "method", ["get_with_downloader", "download_file_to_path", "download_file"]
)
@pytest.mark.parametrize("endpoint", ["redirect", "404", "503", "slow"])
async def test_real_aria2_transport(
    server: str,
    cache_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    endpoint: str,
) -> None:
    output = cache_root / "output"
    if endpoint == "slow":
        monkeypatch.setattr(HttpService, "downloader_timeout", 0.03)

    async def download() -> None:
        if method == "download_file":
            async with HttpService.download_file(server + "/" + endpoint) as path:
                assert json.loads(Path(path).read_bytes()) == {"hello": "world"}
        elif method == "download_file_to_path":
            await HttpService.download_file_to_path(
                server + "/" + endpoint, str(output)
            )
            assert json.loads(output.read_bytes()) == {"hello": "world"}
        else:
            body = await HttpService.get_with_downloader(server + "/" + endpoint)
            assert json.loads(body) == {"hello": "world"}

    if endpoint == "redirect":
        await download()
    else:
        with pytest.raises(HttpRequestError) as raised:
            await download()
        expected = (
            subprocess.TimeoutExpired
            if endpoint == "slow"
            else subprocess.CalledProcessError
        )
        assert isinstance(raised.value.__cause__, expected)
    if method != "download_file_to_path":
        assert list(cache_root.iterdir()) == []
