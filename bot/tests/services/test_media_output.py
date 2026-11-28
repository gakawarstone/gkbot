import json
import shutil
import subprocess
import wave
from pathlib import Path

import pytest

from services.audio import AudioService
from services.cache_dir import CacheDir
from services.slideshow import SlideshowRenderer

pytestmark = pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="ffmpeg and ffprobe are required to verify media output",
)


def probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def write_audio(path: Path) -> None:
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\0\0" * 8000)


async def test_voice_output_is_readable_opus_and_cleans_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.wav"
    write_audio(source)
    cache = tmp_path / "cache"
    cache.mkdir()
    monkeypatch.setattr(CacheDir, "_CacheDir__base_path", str(cache))

    voice = await AudioService.convert_music_to_voice(source.read_bytes())
    output = tmp_path / "voice.ogg"
    output.write_bytes(voice)
    streams = probe(output)["streams"]
    assert len(streams) == 1
    assert streams[0]["codec_name"] == "opus"
    assert float(streams[0]["duration"]) == pytest.approx(1, abs=0.1)
    assert list(cache.iterdir()) == []


@pytest.mark.parametrize("with_audio", [False, True])
async def test_slideshow_output_has_expected_media_properties(
    tmp_path: Path, with_audio: bool
) -> None:
    image = tmp_path / "image.ppm"
    image.write_bytes(b"P6\n32 32\n255\n" + b"\xff\x00\x00" * 32 * 32)
    audio = tmp_path / "source.wav"
    write_audio(audio)
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    output = output_dir / "result.mp4"

    await SlideshowRenderer.make_slideshow_file_from_web(
        [str(image)], str(audio) if with_audio else None, str(output)
    )
    media = probe(output)
    video = next(
        stream for stream in media["streams"] if stream["codec_type"] == "video"
    )
    assert video["codec_name"] == "h264"
    assert video["pix_fmt"] in {"yuv420p", "yuvj420p"}
    assert (video["width"], video["height"]) == (720, 1080)
    assert float(video["duration"]) == pytest.approx(9, abs=0.2)
    assert (
        any(stream["codec_type"] == "audio" for stream in media["streams"])
        is with_audio
    )
