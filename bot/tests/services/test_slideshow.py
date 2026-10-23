import asyncio
import threading
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import AsyncMock

import pytest

from services.audio import AudioService
from services.cache_dir import CacheDir
from services.ffmpeg_runner import FfmpegRunner
from services.slideshow import SlideshowRenderer


@pytest.fixture
async def cache_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(CacheDir, "_CacheDir__base_path", str(tmp_path))
    return tmp_path


@pytest.mark.parametrize("audio_url", [None, "https://example.invalid/audio"])
async def test_slideshow_file_uses_owned_output_directory(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch, audio_url: str | None
) -> None:
    images = AsyncMock()
    audio = AsyncMock()
    run = AsyncMock()
    monkeypatch.setattr(SlideshowRenderer, "download_and_prepare_images", images)
    monkeypatch.setattr(AudioService, "download_and_prepare_audio", audio)
    monkeypatch.setattr(FfmpegRunner, "run", run)
    output_path = str(cache_root / "video.mp4")
    urls = ["https://example.invalid/image"]
    await SlideshowRenderer.make_slideshow_file_from_web(urls, audio_url, output_path)
    images.assert_awaited_once_with(urls, str(cache_root))
    assert run.await_args is not None
    command = run.await_args.args[0]
    assert command[-1] == output_path
    assert str(cache_root / "*.jpg") in command
    if audio_url:
        audio.assert_awaited_once_with(audio_url, str(cache_root))
        assert str(cache_root / "audio.m4a") in command
        assert "-shortest" in command
    else:
        audio.assert_not_awaited()
        assert "-shortest" not in command


@pytest.mark.parametrize("image_count", [1, 2, 3, 4])
async def test_images_keep_order_and_repeat_last_frame_to_at_least_three(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, image_count: int
) -> None:
    urls = [f"https://example.invalid/image/{index}" for index in range(image_count)]
    commands: list[list[str]] = []

    async def prepare(command: list[str]) -> None:
        commands.append(command)
        Path(command[-1]).write_text(command[3])

    monkeypatch.setattr(FfmpegRunner, "run", prepare)
    await SlideshowRenderer.download_and_prepare_images(urls, str(tmp_path))

    assert commands == [
        [
            "ffmpeg",
            "-y",
            "-i",
            url,
            "-vf",
            (
                "scale=trunc(oh*a/2)*2:720,"
                "pad=max(iw\\,ih*9/16):max(ih\\,iw*16/9):(ow-iw)/2:(oh-ih)/2:black"
            ),
            str(tmp_path / f"{index:03d}.jpg"),
        ]
        for index, url in enumerate(urls, start=1)
    ]
    assert [path.read_text() for path in sorted(tmp_path.iterdir())] == (
        urls + [urls[-1]] * max(0, 3 - image_count)
    )


@pytest.mark.parametrize("failure_stage", ["images", "audio", "render"])
async def test_file_render_propagates_errors_and_leaves_caller_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure_stage: str
) -> None:
    error = CalledProcessError(1, "ffmpeg")
    images = AsyncMock(side_effect=error if failure_stage == "images" else None)
    audio = AsyncMock(side_effect=error if failure_stage == "audio" else None)
    run = AsyncMock(side_effect=error if failure_stage == "render" else None)
    monkeypatch.setattr(SlideshowRenderer, "download_and_prepare_images", images)
    monkeypatch.setattr(AudioService, "download_and_prepare_audio", audio)
    monkeypatch.setattr(FfmpegRunner, "run", run)
    existing_file = tmp_path / "caller.txt"
    existing_file.write_bytes(b"keep")

    with pytest.raises(CalledProcessError) as raised:
        await SlideshowRenderer.make_slideshow_file_from_web(
            ["image"], "audio", str(tmp_path / "video.mp4")
        )

    assert raised.value is error
    assert existing_file.read_bytes() == b"keep"
    if failure_stage == "images":
        audio.assert_not_awaited()
    if failure_stage != "render":
        run.assert_not_awaited()


@pytest.mark.parametrize("fail", [False, True])
async def test_slideshow_bytes_compatibility_and_cleanup(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch, fail: bool
) -> None:
    async def generate(urls: list[str], audio: str | None, output: str) -> None:
        Path(output).write_bytes(b"slideshow")
        if fail:
            raise CalledProcessError(1, "ffmpeg")

    monkeypatch.setattr(SlideshowRenderer, "make_slideshow_file_from_web", generate)
    if fail:
        with pytest.raises(CalledProcessError):
            await SlideshowRenderer.make_slideshow_from_web(["image"], None)
    else:
        assert (
            await SlideshowRenderer.make_slideshow_from_web(["image"], None)
            == b"slideshow"
        )
    assert list(cache_root.iterdir()) == []


@pytest.mark.parametrize("audio_input", [None, "audio.m4a"])
def test_slideshow_command_preserves_input_option_order(
    audio_input: str | None,
) -> None:
    audio_options = ["-stream_loop", "-1", "-i", audio_input] if audio_input else []
    assert SlideshowRenderer._build_slideshow_command(
        "*.jpg", audio_input, "out.mp4"
    ) == [
        "ffmpeg",
        "-y",
        "-framerate",
        "1/3",
        "-pattern_type",
        "glob",
        "-i",
        "*.jpg",
        *audio_options,
        "-c:v",
        "libx264",
        *(["-shortest"] if audio_input else []),
        "-vf",
        "scale=720:1080",
        "-r",
        "30",
        "-pix_fmt",
        "yuv420p",
        "out.mp4",
    ]


async def test_cancelled_slideshow_finishes_before_cleanup(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    started = threading.Event()
    release = threading.Event()

    def write(output_path: str) -> None:
        started.set()
        assert release.wait(timeout=5)
        assert Path(output_path).parent.is_dir()
        Path(output_path).write_bytes(b"converted")

    async def run(command: list[str]) -> None:
        await asyncio.to_thread(write, command[-1])

    monkeypatch.setattr(FfmpegRunner, "run", run)
    monkeypatch.setattr(SlideshowRenderer, "download_and_prepare_images", AsyncMock())
    task = asyncio.create_task(
        SlideshowRenderer.make_slideshow_from_web(["image"], None)
    )
    try:
        assert await asyncio.to_thread(started.wait, 5)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        assert len(list(cache_root.iterdir())) == 1
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert list(cache_root.iterdir()) == []


@pytest.mark.parametrize("remove_directory", [False, True])
async def test_slideshow_bytes_cleanup_when_output_is_missing(
    cache_root: Path, monkeypatch: pytest.MonkeyPatch, remove_directory: bool
) -> None:
    async def generate(urls: list[str], audio: str | None, output: str) -> None:
        if remove_directory:
            Path(output).parent.rmdir()

    monkeypatch.setattr(SlideshowRenderer, "make_slideshow_file_from_web", generate)
    with pytest.raises(FileNotFoundError):
        await SlideshowRenderer.make_slideshow_from_web(["image"], None)
    assert list(cache_root.iterdir()) == []
