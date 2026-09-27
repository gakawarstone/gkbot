from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import FSInputFile
from services.ytdlp._options import VideoDownloadOptions
from services.ytdlp.downloader import YtdlpDownloader


def test_tiktok_options_prefer_compact_h264_mp4() -> None:
    format_selector = VideoDownloadOptions.tiktok["format"]

    assert format_selector.startswith(
        "b[ext=mp4][vcodec^=h264][acodec!=none][filesize<20M]"
    )
    assert "[filesize_approx<20M]" in format_selector
    assert "[width<=720]" in format_selector
    assert all("[vcodec^=h264]" in choice for choice in format_selector.split("/"))


async def test_tiktok_download_is_not_transcoded(tmp_path: Path) -> None:
    output_path = tmp_path / "video.mp4"
    options = {"outtmpl": str(output_path)}
    youtube_dl = MagicMock()
    youtube_dl.__enter__.return_value = youtube_dl
    youtube_dl.__exit__.return_value = None

    with (
        patch("services.ytdlp.downloader.yt_dlp.YoutubeDL", return_value=youtube_dl),
        patch("services.ytdlp.downloader.os.path.exists", return_value=True),
        patch(
            "services.ytdlp.downloader.FfmpegService.convert_video",
            new_callable=AsyncMock,
        ) as convert_video,
        patch(
            "services.ytdlp.downloader.FfmpegService.compress_video_if_needed",
            new_callable=AsyncMock,
            return_value=str(output_path),
        ) as compress_video,
    ):
        input_file = await YtdlpDownloader._download_file(
            "https://vt.tiktok.com/ZS4cDkR61/", options
        )

    assert isinstance(input_file, FSInputFile)
    assert input_file.path == str(output_path)
    convert_video.assert_not_awaited()
    compress_video.assert_awaited_once_with(
        str(output_path), max_size_bytes=15 * 1024 * 1024, max_width=720
    )


async def test_instagram_download_keeps_compatibility_transcode(tmp_path: Path) -> None:
    output_path = tmp_path / "video.mp4"
    options = {"outtmpl": str(output_path)}
    youtube_dl = MagicMock()
    youtube_dl.__enter__.return_value = youtube_dl
    youtube_dl.__exit__.return_value = None

    with (
        patch("services.ytdlp.downloader.yt_dlp.YoutubeDL", return_value=youtube_dl),
        patch("services.ytdlp.downloader.os.path.exists", return_value=True),
        patch(
            "services.ytdlp.downloader.FfmpegService.convert_video",
            new_callable=AsyncMock,
        ) as convert_video,
        patch(
            "services.ytdlp.downloader.FfmpegService.compress_video_if_needed",
            new_callable=AsyncMock,
        ) as compress_video,
    ):
        input_file = await YtdlpDownloader._download_file(
            "https://www.instagram.com/reel/example/", options
        )

    converted_path = tmp_path / "video_converted.mp4"
    assert isinstance(input_file, FSInputFile)
    assert input_file.path == str(converted_path)
    convert_video.assert_awaited_once_with(str(output_path), str(converted_path))
    compress_video.assert_not_awaited()
