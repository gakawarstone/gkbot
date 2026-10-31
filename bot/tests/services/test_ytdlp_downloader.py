from unittest.mock import AsyncMock, Mock

import pytest

from services.ytdlp.downloader import YtdlpDownloader
from services.ytdlp.source import DownloadSource


@pytest.mark.parametrize("source", [DownloadSource.YOUTUBE, DownloadSource.VK])
@pytest.mark.parametrize(
    ("metadata", "expected_title"),
    [
        ({"duration": 42}, "Unknown title"),
        ({"title": None}, "Unknown title"),
        ({"title": ""}, "Unknown title"),
        ({"title": "Video title", "duration": 42}, "Video title"),
    ],
)
async def test_get_info_handles_missing_title(
    monkeypatch: pytest.MonkeyPatch,
    source: DownloadSource,
    metadata: dict,
    expected_title: str,
) -> None:
    worker = AsyncMock(return_value=metadata)
    local = Mock(return_value=metadata)
    monkeypatch.setattr("services.ytdlp.downloader.get_info", worker)
    monkeypatch.setattr(YtdlpDownloader, "_extract_info_sync", local)
    url = "https://www.youtube.com/watch?v=xnVZhCPp8dU"

    info = await YtdlpDownloader._get_info(url, source)

    assert info.title == expected_title
    assert info.duration == metadata.get("duration", 0)
    if source.uses_worker:
        worker.assert_awaited_once_with(url)
        local.assert_not_called()
    else:
        local.assert_called_once_with(url)
        worker.assert_not_awaited()


@pytest.mark.parametrize("source", [DownloadSource.YOUTUBE, DownloadSource.VK])
async def test_get_info_rejects_invalid_metadata(
    monkeypatch: pytest.MonkeyPatch, source: DownloadSource
) -> None:
    monkeypatch.setattr(
        "services.ytdlp.downloader.get_info", AsyncMock(return_value=None)
    )
    monkeypatch.setattr(YtdlpDownloader, "_extract_info_sync", Mock(return_value=None))

    with pytest.raises(ValueError, match="yt-dlp returned invalid metadata"):
        await YtdlpDownloader._get_info("https://example.com/video", source)
