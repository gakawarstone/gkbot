import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import FSInputFile

from handlers.user.download.download import DownloadHandler
from services.cache_dir import CacheDir
from services.http import HttpService


@pytest.mark.parametrize("failure", [None, "download", "upload", "cancel"])
async def test_document_download_cleans_up_after_upload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str | None
) -> None:
    monkeypatch.setattr(CacheDir, "_CacheDir__base_path", str(tmp_path))
    error = OSError("transfer failed")

    async def download(url: str, output_path: str) -> None:
        Path(output_path).write_bytes(b"document")
        if failure == "download":
            raise error

    async def upload(document: FSInputFile) -> None:
        assert document.filename == "document.bin"
        await asyncio.sleep(0)
        chunks = [chunk async for chunk in document.read(MagicMock())]
        assert b"".join(chunks) == b"document"
        assert Path(document.path).is_file()
        if failure == "upload":
            raise error
        if failure == "cancel":
            raise asyncio.CancelledError

    monkeypatch.setattr(HttpService, "download_file_to_path", download)
    event = MagicMock()
    event.text = "https://example.invalid/document"
    event.delete = AsyncMock()
    event.answer_document = AsyncMock(side_effect=upload)
    handler = DownloadHandler(
        event=event,
        state=MagicMock(set_state=AsyncMock()),
        data={"file_name": "document.bin"},
    )
    if failure == "cancel":
        with pytest.raises(asyncio.CancelledError):
            await handler.handle()
    elif failure:
        with pytest.raises(OSError) as raised:
            await handler.handle()
        assert raised.value is error
    else:
        await handler.handle()
    if failure == "download":
        event.answer_document.assert_not_awaited()
    else:
        event.answer_document.assert_awaited_once()
    assert list(tmp_path.iterdir()) == []
