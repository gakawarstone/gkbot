from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import FSInputFile, URLInputFile

from services.audio import AudioService
from services.cache_dir import CacheDir
from services.matreshka import MatreshkaService, MatreshkaVideo
from services.video_conversion import VideoConversionService
from services.video_metadata import VideoMetadataService
from services.ytdlp.downloader import YtdlpDownloader, _YtDlpInfo
from services.ytdlp.options_manager import YtDlpOptionsManager


@pytest.mark.parametrize("caller", ["matreshka", "ytdlp"])
@pytest.mark.parametrize("fail", [False, True])
async def test_audio_callers_use_audio_service_and_keep_upload_lifetime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caller: str, fail: bool
) -> None:
    monkeypatch.setattr(CacheDir, "_CacheDir__base_path", str(tmp_path))
    url = "https://example.invalid/audio"
    error = CalledProcessError(1, "ffmpeg")

    async def prepare(audio_url: str, work_dir: str) -> None:
        assert audio_url == url
        Path(work_dir, "audio.m4a").write_bytes(b"audio")
        if fail:
            raise error

    prepare_mock = AsyncMock(side_effect=prepare)
    monkeypatch.setattr(AudioService, "download_and_prepare_audio", prepare_mock)
    if caller == "matreshka":
        video = MatreshkaVideo("id", "title", 12, None, url)
        operation = MatreshkaService.download_audio(video)
    else:
        cache = CacheDir()
        monkeypatch.setattr(
            YtdlpDownloader,
            "_get_info",
            AsyncMock(return_value=_YtDlpInfo(12, "title", 0, 0)),
        )
        monkeypatch.setattr(
            YtDlpOptionsManager,
            "choose_audio_options",
            MagicMock(
                return_value=({"outtmpl": cache.get_file_path("audio.m4a")}, cache)
            ),
        )
        monkeypatch.setattr(
            YtdlpDownloader, "_download_file", AsyncMock(return_value=URLInputFile(url))
        )
        operation = YtdlpDownloader.download_audio("https://youtube.com/watch?v=id")

    if fail:
        with pytest.raises(CalledProcessError) as raised:
            async with operation:
                pytest.fail("Failed preparation must not yield an input file")
        assert raised.value is error
    else:
        async with operation as info:
            assert isinstance(info.input_file, FSInputFile)
            assert Path(info.input_file.path).name == "audio.m4a"
            assert Path(info.input_file.path).read_bytes() == b"audio"
            assert (info.title, info.duration) == ("title", 12)
    prepare_mock.assert_awaited_once()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "error", [None, CalledProcessError(1, "ffprobe"), ValueError("invalid JSON")]
)
async def test_downloader_metadata_fallback_keeps_existing_fields_and_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: Exception | None
) -> None:
    original = _YtDlpInfo(12, "title", None, 640)
    metadata = AsyncMock(
        return_value={"height": 480, "width": 720, "duration": 99}, side_effect=error
    )
    monkeypatch.setattr(VideoMetadataService, "get_video_metadata", metadata)
    path = tmp_path / "video.mp4"
    if isinstance(error, ValueError):
        with pytest.raises(ValueError) as raised:
            await YtdlpDownloader._fill_missing_metadata(original, FSInputFile(path))
        assert raised.value is error
    else:
        result = await YtdlpDownloader._fill_missing_metadata(
            original, FSInputFile(path)
        )
        assert result == (original if error else _YtDlpInfo(12, "title", 480, 640))
    metadata.assert_awaited_once_with(str(path))


@pytest.mark.parametrize(
    "url", ["https://instagram.com/reel/id", "https://tiktok.com/id"]
)
@pytest.mark.parametrize("fail", [False, True])
async def test_downloader_uses_video_conversion_and_returns_converted_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, url: str, fail: bool
) -> None:
    input_path = tmp_path / "video.mp4"
    input_path.write_bytes(b"original")
    output_path = tmp_path / "video_converted.mp4"
    error = CalledProcessError(1, "ffmpeg")
    convert = AsyncMock(side_effect=error if fail else None)
    monkeypatch.setattr(VideoConversionService, "convert_video", convert)
    ydl = MagicMock()
    monkeypatch.setattr("services.ytdlp.downloader.yt_dlp.YoutubeDL", ydl)
    if fail:
        with pytest.raises(CalledProcessError) as raised:
            await YtdlpDownloader._download_file(url, {"outtmpl": str(input_path)})
        assert raised.value is error
    else:
        result = await YtdlpDownloader._download_file(url, {"outtmpl": str(input_path)})
        assert isinstance(result, FSInputFile)
        assert result.path == str(output_path)
    convert.assert_awaited_once_with(str(input_path), str(output_path))
    assert input_path.read_bytes() == b"original"
