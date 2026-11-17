from pathlib import Path
from typing import Any, BinaryIO
from unittest.mock import AsyncMock

import pytest

from services.http import HttpService
from services.litterbox import LitterboxUploader
from services.static import StaticFile


async def test_uncached_static_file_preserves_newlines(tmp_path: Path) -> None:
    path = tmp_path / "text.txt"
    path.write_bytes("Текст\r\nследующая строка\n".encode())

    assert (
        await StaticFile(str(path), cache=False).as_str()
        == "Текст\r\nследующая строка\n"
    )


@pytest.mark.parametrize("failure", [False, True])
async def test_upload_keeps_file_open_until_request_finishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: bool
) -> None:
    path = tmp_path / "upload.bin"
    path.write_bytes(b"contents")
    uploaded: list[BinaryIO] = []

    async def post(url: str, body: dict[str, Any]) -> bytes:
        file = body["fileToUpload"]
        uploaded.append(file)
        assert not file.closed
        assert file.read() == b"contents"
        if failure:
            raise OSError("upload failed")
        return b"https://example.invalid/upload.bin"

    monkeypatch.setattr(HttpService, "post", AsyncMock(side_effect=post))
    if failure:
        with pytest.raises(OSError, match="upload failed"):
            await LitterboxUploader.upload_with_path(str(path))
    else:
        assert (
            await LitterboxUploader.upload_with_path(str(path))
            == "https://example.invalid/upload.bin"
        )
    assert len(uploaded) == 1
    assert uploaded[0].closed
