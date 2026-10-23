from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from aiogram.types import FSInputFile, URLInputFile

from services.cache_dir import CacheDir
from services.ffmpeg import FfmpegService
from services.ytdlp import YtdlpDownloader, downloader
from services.ytdlp._options import AudioDownloadOptions, VideoDownloadOptions
from services.ytdlp.options_manager import YtDlpOptionsManager
from services.ytdlp.source import DownloadSource, classify_source


@pytest.fixture
async def cache_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(CacheDir, "_CacheDir__base_path", str(tmp_path))
    return tmp_path


@pytest.mark.parametrize(
    ("source", "preset"),
    [
        (DownloadSource.YOUTUBE, VideoDownloadOptions.youtube),
        (DownloadSource.YOUTUBE_SHORTS, VideoDownloadOptions.youtube_shorts),
        (DownloadSource.TIKTOK, VideoDownloadOptions.tiktok),
        (DownloadSource.INSTAGRAM, VideoDownloadOptions.default),
        (DownloadSource.INSTAGRAM_REEL, VideoDownloadOptions.default),
        (DownloadSource.VK, VideoDownloadOptions.vk),
        (DownloadSource.VK_CLIP, VideoDownloadOptions.tiktok),
        (DownloadSource.UNKNOWN, VideoDownloadOptions.default),
    ],
)
async def test_video_options(
    cache_root: Path, source: DownloadSource, preset: dict[str, Any]
) -> None:
    opts, cache = YtDlpOptionsManager.choose_video_options(source)
    try:
        assert Path(cache.path).parent == cache_root
        assert opts.pop("outtmpl") == cache.get_file_path("video.mp4")
        assert opts == preset
        assert "outtmpl" not in preset
    finally:
        cache.delete()


@pytest.mark.parametrize("source", list(DownloadSource))
async def test_audio_options(cache_root: Path, source: DownloadSource) -> None:
    preset = (
        AudioDownloadOptions.vk
        if source in (DownloadSource.VK, DownloadSource.VK_CLIP)
        else AudioDownloadOptions.youtube
    )
    opts, cache = YtDlpOptionsManager.choose_audio_options(source)
    try:
        assert Path(cache.path).parent == cache_root
        assert opts.pop("outtmpl") == cache.get_file_path("audio.m4a")
        assert opts == preset
        assert "outtmpl" not in preset
    finally:
        cache.delete()


@pytest.mark.parametrize("media", ["audio", "video"])
@pytest.mark.parametrize(
    ("url", "uses_worker", "converts_video"),
    [
        ("https://www.youtube.com/watch?v=abc", True, False),
        ("http://youtu.be/abc", True, False),
        ("https://m.youtube.com/shorts/abc", True, False),
        ("https://vm.tiktok.com/abc/", False, True),
        ("https://www.instagram.com/reel/abc/", False, True),
        ("https://instagram.com/p/abc/", False, False),
        ("https://vk.com/video-123_456", False, False),
        ("https://vkvideo.ru/video-123_456", False, False),
        ("https://vk.com/clip-123_456", False, False),
        ("https://m.vkvideo.ru/clip123_456", False, False),
        ("https://example.org/video", False, False),
        ("https://youtubeevil.example/tiktok.com/video", False, False),
        ("https://example.org/instagram.com/reel/abc", False, False),
    ],
)
async def test_download_classifies_once_and_routes_all_stages(
    cache_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    media: str,
    url: str,
    uses_worker: bool,
    converts_video: bool,
) -> None:
    raw_info = {"title": "Example", "duration": 12, "height": 720, "width": 1280}
    classifier = Mock(wraps=classify_source)
    worker_info = AsyncMock(return_value=raw_info)
    worker_download = AsyncMock(return_value="https://cdn.example/video")
    local = MagicMock()
    local.extract_info.return_value = raw_info

    def make_local(opts: dict[str, Any] | None = None) -> MagicMock:
        if opts is not None:
            local.download.side_effect = lambda _: Path(opts["outtmpl"]).touch()
        context = MagicMock()
        context.__enter__.return_value = local
        return context

    convert = AsyncMock()
    prepare_audio = AsyncMock()
    monkeypatch.setattr(downloader, "classify_source", classifier)
    monkeypatch.setattr(downloader, "get_info", worker_info)
    monkeypatch.setattr(downloader, "download_video", worker_download)
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", make_local)
    monkeypatch.setattr(FfmpegService, "convert_video", convert)
    monkeypatch.setattr(FfmpegService, "download_and_prepare_audio", prepare_audio)
    operation = (
        YtdlpDownloader.download_audio(url)
        if media == "audio"
        else YtdlpDownloader.download_video(url)
    )
    async with operation as result:
        classifier.assert_called_once_with(url)
        assert result.duration == 12
        assert result.title == "Example"
        assert len(list(cache_root.iterdir())) == 1
        if uses_worker:
            worker_info.assert_awaited_once_with(url)
            assert worker_download.await_args is not None
            assert worker_download.await_args.args[0] == url
            local.extract_info.assert_not_called()
            local.download.assert_not_called()
        else:
            worker_info.assert_not_awaited()
            worker_download.assert_not_awaited()
            local.extract_info.assert_called_once_with(url, download=False)
            local.download.assert_called_once_with(url)
        if media == "video" and uses_worker:
            assert isinstance(result.input_file, URLInputFile)
        else:
            assert isinstance(result.input_file, FSInputFile)
        if converts_video:
            assert convert.await_args is not None
            original, converted = convert.await_args.args
            assert (
                Path(original).name == f"{media}.{'m4a' if media == 'audio' else 'mp4'}"
            )
            assert converted == str(Path(original).with_name(f"{media}_converted.mp4"))
        else:
            convert.assert_not_awaited()
        if media == "audio" and uses_worker:
            assert isinstance(result.input_file, FSInputFile)
            assert prepare_audio.await_args is not None
            assert prepare_audio.await_args.args == (
                "https://cdn.example/video",
                str(Path(result.input_file.path).parent),
            )
        else:
            prepare_audio.assert_not_awaited()
    assert list(cache_root.iterdir()) == []
