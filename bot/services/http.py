import asyncio
import json
import subprocess
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any, ClassVar, cast

import aiohttp
from yarl import URL

from services.cache_dir import CacheDir
from utils.async_cleanup import wait_for_completion

_headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        "Chrome/106.0.0.0 Safari/537.36"
    ),
}


class HttpRequestError(Exception):
    """A transport, HTTP status, response decoding, or response size failure."""


class ResponseTooLargeError(ValueError):
    """The decoded response exceeds the configured in-memory limit."""


class HttpService:
    headers = _headers
    timeout = aiohttp.ClientTimeout(
        total=120, connect=10, sock_connect=10, sock_read=30
    )
    max_body_bytes = 50 * 1024 * 1024
    max_json_bytes = 8 * 1024 * 1024
    downloader_timeout = 120
    _session: ClassVar[aiohttp.ClientSession | None] = None

    @classmethod
    def _get_session(cls) -> aiohttp.ClientSession:
        # No await between checking and creating: concurrent requests share it.
        if cls._session is None or cls._session.closed:
            cls._session = aiohttp.ClientSession(
                timeout=cls.timeout, cookie_jar=aiohttp.DummyCookieJar()
            )
        return cls._session

    @classmethod
    async def close(cls) -> None:
        """Release the application session after all request users have stopped."""
        if cls._session is not None:
            await wait_for_completion(cls._session.close())
            cls._session = None

    @classmethod
    @asynccontextmanager
    async def _request(
        cls,
        method: str,
        url: str,
        headers: dict[str, str] | None,
        *,
        encoded: bool = False,
        **kwargs: Any,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        try:
            request_url = URL(url, encoded=encoded)
        except ValueError as error:
            raise HttpRequestError(f"Invalid request URL: {error}") from error
        try:
            async with cls._get_session().request(
                method, request_url, headers=headers, **kwargs
            ) as response:
                response.raise_for_status()
                yield response
        except (
            aiohttp.ClientError,
            TimeoutError,
            ResponseTooLargeError,
        ) as error:
            raise HttpRequestError(f"{method} request failed: {error}") from error

    @staticmethod
    async def _read_body(response: aiohttp.ClientResponse, limit: int) -> bytes:
        if (
            not response.headers.get("Content-Encoding")
            and response.content_length is not None
            and response.content_length > limit
        ):
            raise ResponseTooLargeError(f"Response exceeds {limit} bytes")
        body = bytearray()
        # Count actual decoded bytes: Content-Length may be missing or compressed.
        async for chunk in response.content.iter_chunked(64 * 1024):
            if len(body) + len(chunk) > limit:
                raise ResponseTooLargeError(f"Response exceeds {limit} bytes")
            body.extend(chunk)
        return bytes(body)

    @classmethod
    async def _read_json(cls, response: aiohttp.ClientResponse) -> dict:
        content_type = response.content_type
        if content_type != "application/json" and not (
            content_type.startswith("application/") and content_type.endswith("+json")
        ):
            raise aiohttp.ContentTypeError(
                response.request_info,
                response.history,
                message=f"Unexpected JSON content type: {content_type}",
                headers=response.headers,
            )
        body = await cls._read_body(response, cls.max_json_bytes)
        try:
            return cast(dict, json.loads(body.decode(response.charset or "utf-8")))
        except (ValueError, LookupError, RecursionError) as error:
            raise HttpRequestError(f"Invalid JSON response: {error}") from error

    @classmethod
    async def get(cls, url: str, headers: dict[str, str] | None = headers) -> bytes:
        async with cls._request("GET", url, headers, encoded=True) as response:
            return await cls._read_body(response, cls.max_body_bytes)

    @classmethod
    async def get_redirected_url(
        cls, url: str, headers: dict[str, str] | None = headers
    ) -> str:
        async with cls._request("GET", url, headers) as response:
            return response.url.human_repr()

    @classmethod
    async def extract_cookies(
        cls, url: str, headers: dict[str, str] | None = headers
    ) -> SimpleCookie:
        async with cls._request("GET", url, headers) as response:
            return response.cookies

    @classmethod
    async def get_json(cls, url: str) -> dict:
        async with cls._request("GET", url, cls.headers) as response:
            return await cls._read_json(response)

    @classmethod
    async def post(
        cls, url: str, body: dict, headers: dict[str, str] | None = headers
    ) -> bytes:
        async with cls._request("POST", url, headers, data=body) as response:
            return await cls._read_body(response, cls.max_body_bytes)

    @classmethod
    async def post_json(
        cls, url: str, body: dict, headers: dict[str, str] | None = headers
    ) -> dict:
        async with cls._request("POST", url, headers, json=body) as response:
            return await cls._read_json(response)

    @classmethod
    async def _download(
        cls, url: str, output_path: str, headers: dict[str, str] | None = None
    ) -> None:
        path = Path(output_path).absolute()
        command = [
            "aria2c",
            "--no-conf=true",
            "--quiet=true",
            "--allow-overwrite=true",
            "--auto-file-renaming=false",
            "--connect-timeout=10",
            "--timeout=30",
            "--max-tries=1",
        ]
        for header_name, header_value in (headers or {}).items():
            command.extend(["--header", f"{header_name}: {header_value}"])
        command.extend(["--dir", str(path.parent), "--out", path.name, "--", url])
        try:
            # subprocess.run kills and reaps on timeout. Shielding also prevents
            # a cancelled caller from deleting a directory still used by aria2.
            await wait_for_completion(
                asyncio.to_thread(
                    subprocess.run,
                    command,
                    check=True,
                    timeout=cls.downloader_timeout,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise HttpRequestError(f"Download failed: {error}") from error

    @staticmethod
    def _read_downloaded_body(file_path: str, limit: int) -> bytes:
        with open(file_path, "rb") as response_file:
            body = response_file.read(limit + 1)
        if len(body) > limit:
            raise ResponseTooLargeError(f"Response exceeds {limit} bytes")
        return body

    @classmethod
    async def get_with_downloader(
        cls, url: str, headers: dict[str, str] | None = None
    ) -> bytes:
        cache_dir = CacheDir()
        try:
            file_path = cache_dir.get_file_path("response")
            await cls._download(url, file_path, headers)
            return await wait_for_completion(
                asyncio.to_thread(
                    cls._read_downloaded_body, file_path, cls.max_body_bytes
                )
            )
        except (OSError, ResponseTooLargeError) as error:
            raise HttpRequestError(f"Downloaded response failed: {error}") from error
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
        await cls._download(url, output_path)
