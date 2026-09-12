from pathlib import Path
from unittest.mock import AsyncMock, patch

from services.ffmpeg import FfmpegService


async def test_small_video_does_not_get_reencoded(tmp_path: Path) -> None:
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"small video")

    with patch.object(
        FfmpegService, "_compress_video_to_size", new_callable=AsyncMock
    ) as compress_video:
        result = await FfmpegService.compress_video_if_needed(
            str(video_path), max_size_bytes=15 * 1024 * 1024, max_width=720
        )

    assert result == str(video_path)
    compress_video.assert_not_awaited()


async def test_large_video_uses_size_limited_encoding(tmp_path: Path) -> None:
    video_path = tmp_path / "video.mp4"

    with (
        patch("services.ffmpeg.os.path.getsize", return_value=20 * 1024 * 1024),
        patch.object(
            FfmpegService, "_compress_video_to_size", new_callable=AsyncMock
        ) as compress_video,
    ):
        result = await FfmpegService.compress_video_if_needed(
            str(video_path), max_size_bytes=15 * 1024 * 1024, max_width=720
        )

    compressed_path = tmp_path / "video_compressed.mp4"
    assert result == str(compressed_path)
    compress_video.assert_awaited_once_with(
        str(video_path), str(compressed_path), 15 * 1024 * 1024, 720
    )


async def test_size_limited_encoding_calculates_two_pass_bitrate() -> None:
    with (
        patch.object(
            FfmpegService,
            "get_video_metadata",
            new_callable=AsyncMock,
            return_value={"duration": 60},
        ),
        patch.object(
            FfmpegService, "_run_command", new_callable=AsyncMock
        ) as run_command,
        patch("services.ffmpeg.os.remove"),
    ):
        await FfmpegService._compress_video_to_size(
            "input.mp4", "output.mp4", max_size_bytes=15 * 1024 * 1024, max_width=720
        )

    first_pass, second_pass = [call.args[0] for call in run_command.await_args_list]
    assert first_pass[first_pass.index("-pass") + 1] == "1"
    assert "-an" in first_pass
    assert second_pass[second_pass.index("-pass") + 1] == "2"
    assert second_pass[second_pass.index("-b:v") + 1] == "1843322"
    assert second_pass[second_pass.index("-b:a") + 1] == "128000"
