from typing import Optional
from yarl import URL
import subprocess
from http.cookies import SimpleCookie

import aiohttp
from aiohttp.client_exceptions import ClientConnectorError, ContentTypeError, InvalidURL

from utils.async_wrapper import async_wrap
from services.cache_dir import CacheDir

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
    async def get(cls, url: str, headers: Optional[dict] = headers) -> bytes:
        async with aiohttp.ClientSession(conn_timeout=None) as session:
            try:
                async with session.get(
                    URL(url, encoded=True), headers=headers
                ) as response:
                    return await response.content.read()
            except (ClientConnectorError, InvalidURL):
                raise HttpRequestError

    @classmethod
    async def get_redirected_url(
        cls, url: str, headers: Optional[dict] = headers
    ) -> str:
        async with aiohttp.ClientSession(conn_timeout=None) as session:
            try:
                async with session.get(url, headers=headers) as response:
                    return response.url.human_repr()
            except (ClientConnectorError, InvalidURL):
                raise HttpRequestError

    @classmethod
    async def extract_cookies(cls, url: str, headers: Optional[dict] = headers) -> SimpleCookie:
        async with aiohttp.ClientSession(conn_timeout=None) as session:
            try:
                async with session.get(url, headers=headers) as response:
                    return response.cookies
            except ClientConnectorError:
                raise HttpRequestError

    @classmethod
    async def get_json(cls, url: str) -> dict:
        async with aiohttp.ClientSession(conn_timeout=None) as session:
            try:
                async with session.get(url, headers=cls.headers) as response:
                    return await response.json()
            except (ClientConnectorError, ContentTypeError):
                raise HttpRequestError

    @classmethod
    async def post(
        cls, url: str, body: dict, headers: Optional[dict] = headers
    ) -> bytes:
        async with aiohttp.ClientSession(conn_timeout=None) as session:
            try:
                async with session.post(url, data=body, headers=headers) as response:
                    return await response.content.read()
            except ClientConnectorError:
                raise HttpRequestError

    @classmethod
    async def post_json(
        cls, url: str, body: dict, headers: Optional[dict] = headers
    ) -> dict:
        async with aiohttp.ClientSession(conn_timeout=None) as session:
            try:
                async with session.post(url, json=body, headers=headers) as response:
                    return await response.json()
            except ClientConnectorError:
                raise HttpRequestError

    @classmethod
    async def download_file(cls, url: str) -> str:
        cache_dir = CacheDir()
        file_path = cache_dir.path + "/file"
        await cls.download_file_to_path(url, file_path)
        return file_path

    @classmethod
    async def download_file_to_path(cls, url: str, output_path: str):
        command = ["aria2c", "-x16", "-s16", "-k1M", url, "-o", output_path]
        await async_wrap(subprocess.call)(command)
