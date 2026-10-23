import json
from subprocess import CalledProcessError, CompletedProcess
from unittest.mock import AsyncMock

import pytest

from services.ffmpeg_runner import FfmpegRunner
from services.video_metadata import VideoMetadataService


@pytest.mark.parametrize(
    ("probe_output", "expected"),
    [
        ({"streams": []}, {}),
        ({}, {}),
        (
            {"streams": [{"width": 720, "height": "1080", "duration": "12.9"}]},
            {"width": 720, "height": 1080, "duration": 12},
        ),
        ({"streams": [{"width": 720, "duration": "N/A"}]}, {"width": 720}),
        ({"streams": [{"width": 0, "height": None, "duration": 0}]}, {}),
        ({"streams": [{"height": 480}, {"width": 720}]}, {"height": 480}),
    ],
)
async def test_metadata_delegates_to_runner_and_preserves_parsing(
    monkeypatch: pytest.MonkeyPatch,
    probe_output: dict,
    expected: dict[str, int],
) -> None:
    run = AsyncMock(
        return_value=CompletedProcess([], 0, stdout=json.dumps(probe_output))
    )
    monkeypatch.setattr(FfmpegRunner, "run", run)
    assert await VideoMetadataService.get_video_metadata("input file.mp4") == expected
    run.assert_awaited_once_with(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,duration",
            "-of",
            "json",
            "input file.mp4",
        ],
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    "output", ["invalid json", '{"streams": [{"width": "invalid"}]}']
)
async def test_metadata_preserves_parse_failure(
    monkeypatch: pytest.MonkeyPatch, output: str
) -> None:
    monkeypatch.setattr(
        FfmpegRunner,
        "run",
        AsyncMock(return_value=CompletedProcess([], 0, stdout=output)),
    )
    with pytest.raises(ValueError):
        await VideoMetadataService.get_video_metadata("input.mp4")


@pytest.mark.parametrize(
    "error", [CalledProcessError(3, "ffprobe"), FileNotFoundError("ffprobe")]
)
async def test_metadata_preserves_process_failure(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    monkeypatch.setattr(FfmpegRunner, "run", AsyncMock(side_effect=error))
    with pytest.raises(type(error)) as raised:
        await VideoMetadataService.get_video_metadata("input.mp4")
    assert raised.value is error
