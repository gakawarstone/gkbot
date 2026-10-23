from subprocess import CalledProcessError
from unittest.mock import AsyncMock

import pytest

from services.ffmpeg_runner import FfmpegRunner
from services.video_conversion import VideoConversionService


async def test_video_conversion_delegates_to_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = AsyncMock()
    monkeypatch.setattr(FfmpegRunner, "run", run)
    assert (
        await VideoConversionService.convert_video("input file.mp4", "output.mp4")
        is None
    )
    run.assert_awaited_once_with(
        [
            "ffmpeg",
            "-y",
            "-i",
            "input file.mp4",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-threads",
            "1",
            "-c:a",
            "aac",
            "-pix_fmt",
            "yuv420p",
            "output.mp4",
        ]
    )


@pytest.mark.parametrize(
    "error", [CalledProcessError(3, "ffmpeg"), FileNotFoundError("ffmpeg")]
)
async def test_service_preserves_runner_failure(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    monkeypatch.setattr(FfmpegRunner, "run", AsyncMock(side_effect=error))
    with pytest.raises(type(error)) as raised:
        await VideoConversionService.convert_video("input.mp4", "output.mp4")
    assert raised.value is error
