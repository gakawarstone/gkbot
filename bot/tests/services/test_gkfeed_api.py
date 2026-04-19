import aiohttp
import pytest

from services.gkfeed import GkfeedApi, GkfeedCredentials, GkfeedRequestError


class FakeResponse:
    def __init__(self, payload: bytes | Exception) -> None:
        self._payload = payload

    async def __aenter__(self) -> "FakeResponse":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    def raise_for_status(self) -> None:
        return None

    async def read(self) -> bytes:
        if isinstance(self._payload, Exception):
            raise self._payload

        return self._payload


class FakeClientSession:
    def __init__(self, payloads: list[bytes | Exception], **kwargs) -> None:
        self._payloads = payloads

    async def __aenter__(self) -> "FakeClientSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    def get(self, url: str, auth: aiohttp.BasicAuth) -> FakeResponse:
        return FakeResponse(self._payloads.pop(0))


@pytest.mark.asyncio
async def test_get_html_retries_after_payload_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads: list[bytes | Exception] = [
        aiohttp.ClientPayloadError("broken body"),
        b'{"items": []}',
    ]

    monkeypatch.setattr(
        aiohttp,
        "ClientSession",
        lambda **kwargs: FakeClientSession(payloads, **kwargs),
    )

    api = GkfeedApi(GkfeedCredentials(login="login", password="password"))

    response = await api._get_html("https://example.com/get_items")

    assert response == b'{"items": []}'


@pytest.mark.asyncio
async def test_get_html_raises_after_retries_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads: list[bytes | Exception] = [
        aiohttp.ClientPayloadError("broken body"),
        aiohttp.ClientPayloadError("broken body"),
        aiohttp.ClientPayloadError("broken body"),
    ]

    monkeypatch.setattr(
        aiohttp,
        "ClientSession",
        lambda **kwargs: FakeClientSession(payloads, **kwargs),
    )

    api = GkfeedApi(GkfeedCredentials(login="login", password="password"))

    with pytest.raises(GkfeedRequestError):
        await api._get_html("https://example.com/get_items")


@pytest.mark.asyncio
async def test_get_html_uses_cached_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads: list[bytes | Exception] = [b'{"items": []}']

    monkeypatch.setattr(
        aiohttp,
        "ClientSession",
        lambda **kwargs: FakeClientSession(payloads, **kwargs),
    )

    api = GkfeedApi(GkfeedCredentials(login="login", password="password"))

    first_response = await api._get_html("https://example.com/get_items")
    second_response = await api._get_html("https://example.com/get_items")

    assert first_response == second_response == b'{"items": []}'
    assert payloads == []


@pytest.mark.asyncio
async def test_get_html_refreshes_expired_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads: list[bytes | Exception] = [
        b'{"items": [1]}',
        b'{"items": [2]}',
    ]
    timestamps = iter([100.0, 161.0, 161.0])

    monkeypatch.setattr(
        aiohttp,
        "ClientSession",
        lambda **kwargs: FakeClientSession(payloads, **kwargs),
    )
    monkeypatch.setattr(
        GkfeedApi,
        "_get_current_timestamp",
        staticmethod(lambda: next(timestamps)),
    )

    api = GkfeedApi(GkfeedCredentials(login="login", password="password"))

    first_response = await api._get_html("https://example.com/get_items")
    second_response = await api._get_html("https://example.com/get_items")

    assert first_response == b'{"items": [1]}'
    assert second_response == b'{"items": [2]}'
