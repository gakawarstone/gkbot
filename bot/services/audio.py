from pathlib import Path

from services.cache_dir import CacheDir
from services.ffmpeg_runner import FfmpegRunner
from utils.async_cleanup import wait_for_completion


class AudioService:
    """Convert music to voice and prepare audio in caller-owned directories."""

    @staticmethod
    async def convert_music_to_voice(music: bytes) -> bytes:
        """Return Ogg Opus bytes, waiting for conversion before temporary cleanup."""
        cache_dir = CacheDir()
        try:
            cache_dir.save_file("music.mp3", music)

            command = FfmpegRunner.build_command(
                inputs=[cache_dir.get_file_path("music.mp3")],
                output=cache_dir.get_file_path("voice.ogg"),
                props=["-acodec", "libopus"],
            )

            await wait_for_completion(FfmpegRunner.run(command))
            return Path(cache_dir.get_file_path("voice.ogg")).read_bytes()
        finally:
            cache_dir.delete()

    @staticmethod
    async def download_and_prepare_audio(audio_url: str, work_dir_path: str) -> None:
        """Write audio.m4a into an existing caller-owned directory."""
        command = FfmpegRunner.build_command(
            inputs=[audio_url],
            output=f"{work_dir_path}/audio.m4a",
            props=["-vn"],
        )
        await FfmpegRunner.run(command)
