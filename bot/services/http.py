import aiohttp
from aiohttp.client_exceptions import ClientConnectorError

_headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        "Chrome/106.0.0.0 Safari/537.36"
    ),
}


class HttpRequestError(Exception):
    "Http request error"


class HttpService:
    headers = _headers

    @classmethod
    async def get(cls, url: str) -> bytes:
        async with aiohttp.ClientSession(conn_timeout=None) as session:
            try:
                async with session.get(url, headers=cls.headers) as response:
                    return await response.content.read()
            except ClientConnectorError:
                raise HttpRequestError

    @classmethod
    async def post(cls, url: str, body: dict) -> dict:
        async with aiohttp.ClientSession(conn_timeout=None) as session:
            try:
                async with session.post(url, params=body) as response:
                    return await response.json()
            except ClientConnectorError:
                raise HttpRequestError
