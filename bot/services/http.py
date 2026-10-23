import asyncio
import subprocess
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http.cookies import SimpleCookie
from pathlib import Path

import aiohttp
from aiohttp.client_exceptions import ClientConnectorError, ContentTypeError, InvalidURL
from yarl import URL

from services.cache_dir import CacheDir
from utils.async_cleanup import wait_for_completion
from utils.async_wrapper import async_wrap

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
    async def get(cls, url: str, headers: dict | None = headers) -> bytes:
        async with aiohttp.ClientSession(conn_timeout=None) as session:
            try:
                async with session.get(
                    URL(url, encoded=True), headers=headers
                ) as response:
                    return await response.content.read()
            except (ClientConnectorError, InvalidURL):
                raise HttpRequestError

    @classmethod
    async def get_redirected_url(cls, url: str, headers: dict | None = headers) -> str:
        async with aiohttp.ClientSession(conn_timeout=None) as session:
            try:
                async with session.get(url, headers=headers) as response:
                    return response.url.human_repr()
            except (ClientConnectorError, InvalidURL):
                raise HttpRequestError

    @classmethod
    async def extract_cookies(
        cls, url: str, headers: dict | None = headers
    ) -> SimpleCookie:
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
    async def post(cls, url: str, body: dict, headers: dict | None = headers) -> bytes:
        async with aiohttp.ClientSession(conn_timeout=None) as session:
            try:
                async with session.post(url, data=body, headers=headers) as response:
                    return await response.content.read()
            except ClientConnectorError:
                raise HttpRequestError

    @classmethod
    async def post_json(
        cls, url: str, body: dict, headers: dict | None = headers
    ) -> dict:
        async with aiohttp.ClientSession(conn_timeout=None) as session:
            try:
                async with session.post(url, json=body, headers=headers) as response:
                    return await response.json()
            except ClientConnectorError:
                raise HttpRequestError

    @classmethod
    async def get_with_downloader(
        cls, url: str, headers: dict[str, str] | None = None
    ) -> bytes:
        cache_dir = CacheDir()
        file_path = cache_dir.get_file_path("response")
        command = [
            "aria2c",
            "--quiet=true",
            "--allow-overwrite=true",
            "--auto-file-renaming=false",
        ]
        for header_name, header_value in (headers or {}).items():
            command.extend(["--header", f"{header_name}: {header_value}"])
        command.extend(["--dir", cache_dir.path, "--out", "response", url])

        try:
            return_code = await async_wrap(subprocess.call)(command)
            if return_code != 0:
                raise HttpRequestError

            return await wait_for_completion(
                asyncio.to_thread(Path(file_path).read_bytes)
            )
        except OSError as error:
            raise HttpRequestError from error
        finally:
            cache_dir.delete()

    @classmethod
    @asynccontextmanager
    async def download_file(cls, url: str) -> AsyncIterator[str]:
        """Keep the downloaded path alive only inside the caller's async with."""
        cache_dir = CacheDir()
        try:
            file_path = cache_dir.get_file_path("file")
            await wait_for_completion(cls.download_file_to_path(url, file_path))
            yield file_path
        finally:
            cache_dir.delete()

    @classmethod
    async def download_file_to_path(cls, url: str, output_path: str) -> None:
        """Download to a caller-owned path; the caller handles its lifetime."""
        command = ["aria2c", "-x16", "-s16", "-k1M", url, "-o", output_path]
        await async_wrap(subprocess.call)(command)
