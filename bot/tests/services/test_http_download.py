import asyncio
import threading
from pathlib import Path

import pytest

from services.cache_dir import CacheDir
from services.http import HttpService


@pytest.fixture
def cache_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(CacheDir, "_CacheDir__base_path", str(tmp_path))
    return tmp_path


@pytest.mark.parametrize("failure", [None, "download", "consumer", "removed"])
async def test_download_file_owns_directory(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch, failure: str | None
) -> None:
    error = OSError("download or consumer failed")

    async def download(url: str, output_path: str) -> None:
        assert url == "https://example.invalid/document"
        Path(output_path).write_bytes(b"document")
        if failure == "download":
            raise error

    async def consume() -> None:
        async with HttpService.download_file(
            "https://example.invalid/document"
        ) as file_path:
            assert Path(file_path).read_bytes() == b"document"
            if failure == "removed":
                Path(file_path).unlink()
                Path(file_path).parent.rmdir()
            if failure in ("consumer", "removed"):
                raise error

    monkeypatch.setattr(HttpService, "download_file_to_path", download)
    if failure:
        with pytest.raises(OSError) as raised:
            await consume()
        assert raised.value is error
    else:
        await consume()
    assert list(cache_root.iterdir()) == []


async def test_cancelled_download_finishes_writing_before_cleanup(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    started = threading.Event()
    release = threading.Event()

    def write(output_path: str) -> None:
        started.set()
        assert release.wait(timeout=5)
        assert Path(output_path).parent.is_dir()
        Path(output_path).write_bytes(b"document")

    async def download(url: str, output_path: str) -> None:
        await asyncio.to_thread(write, output_path)

    async def consume() -> None:
        async with HttpService.download_file("https://example.invalid/document"):
            pytest.fail("Cancelled download must not yield a path")

    monkeypatch.setattr(HttpService, "download_file_to_path", download)
    task = asyncio.create_task(consume())
    try:
        assert await asyncio.to_thread(started.wait, 5)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        assert len(list(cache_root.iterdir())) == 1
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert list(cache_root.iterdir()) == []
