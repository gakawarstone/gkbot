import asyncio
import json
import os
import shutil
import subprocess
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any, ClassVar

from services.cache_dir import CacheDir
from utils.async_cleanup import wait_for_completion
from utils.async_wrapper import async_wrap


class FfmpegService:
    SLIDESHOW_WIDTH = 720
    SLIDESHOW_HEIGHT = 1080

    _semaphore = asyncio.Semaphore(1)

    __resize_image_options: ClassVar[list[str]] = [
        "-vf",
        (
            "scale=trunc(oh*a/2)*2:720,"
            "pad=max(iw\\,ih*9/16):max(ih\\,iw*16/9):(ow-iw)/2:(oh-ih)/2:black"
        ),
    ]
    __make_slideshow_options: ClassVar[list[str]] = [
        "-c:v",
        "libx264",
        "-shortest",
        "-vf",
        f"scale={SLIDESHOW_WIDTH}:{SLIDESHOW_HEIGHT}",
        "-r",
        "30",
        "-pix_fmt",
        "yuv420p",
    ]

    __convert_to_voice_options: ClassVar[list[str]] = ["-acodec", "libopus"]

    @classmethod
    async def convert_music_to_voice(cls, music: bytes) -> bytes:
        cache_dir = CacheDir()
        try:
            cache_dir.save_file("music.mp3", music)

            command = cls._build_command(
                inputs=[cache_dir.get_file_path("music.mp3")],
                output=cache_dir.get_file_path("voice.ogg"),
                props=cls.__convert_to_voice_options,
            )

            await wait_for_completion(cls._run_command(command))
            return await wait_for_completion(
                asyncio.to_thread(Path(cache_dir.get_file_path("voice.ogg")).read_bytes)
            )
        finally:
            cache_dir.delete()

    @classmethod
    async def convert_video(cls, input_path: str, output_path: str) -> None:
        command = cls._build_command(
            inputs=[input_path],
            output=output_path,
            props=[
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
            ],
        )
        await cls._run_command(command)

    @classmethod
    async def compress_video_if_needed(
        cls, input_path: str, max_size_bytes: int, max_width: int
    ) -> str:
        if os.path.getsize(input_path) <= max_size_bytes:
            return input_path

        base, _ = os.path.splitext(input_path)
        output_path = f"{base}_compressed.mp4"
        await cls._compress_video_to_size(
            input_path, output_path, max_size_bytes, max_width
        )
        return output_path

    @classmethod
    async def _compress_video_to_size(
        cls,
        input_path: str,
        output_path: str,
        max_size_bytes: int,
        max_width: int,
    ) -> None:
        metadata = await cls.get_video_metadata(input_path)
        duration = metadata.get("duration", 0)
        if duration <= 0:
            raise ValueError("Video duration is required for size-limited encoding")

        # Leave headroom for the MP4 container so the finished file stays below
        # the configured limit rather than merely targeting it on average.
        total_bitrate = int(max_size_bytes * 8 * 0.94 / duration)
        audio_bitrate = min(128_000, max(32_000, total_bitrate // 10))
        video_bitrate = max(100_000, total_bitrate - audio_bitrate)
        passlog_path = f"{output_path}.passlog"
        video_options = [
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-b:v",
            str(video_bitrate),
            "-vf",
            f"scale='min({max_width},iw)':-2",
            "-pix_fmt",
            "yuv420p",
            "-passlogfile",
            passlog_path,
        ]

        first_pass = cls._build_command(
            inputs=[input_path],
            output=os.devnull,
            props=video_options + ["-pass", "1", "-an", "-f", "null"],
        )
        second_pass = cls._build_command(
            inputs=[input_path],
            output=output_path,
            props=video_options
            + [
                "-pass",
                "2",
                "-c:a",
                "aac",
                "-b:a",
                str(audio_bitrate),
                "-movflags",
                "+faststart",
            ],
        )

        try:
            await cls._run_command(first_pass)
            await cls._run_command(second_pass)
        finally:
            for suffix in ("-0.log", "-0.log.mbtree"):
                Path(passlog_path + suffix).unlink(missing_ok=True)

    @classmethod
    async def get_video_metadata(cls, input_path: str) -> dict[str, int]:
        command = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,duration:format=duration",
            "-of",
            "json",
            input_path,
        ]
        result = await cls._run_command(command, capture_output=True, text=True)
        probe_data = json.loads(result.stdout)
        streams = probe_data.get("streams", [])
        if not streams:
            return {}

        stream = streams[0]
        metadata = {}
        for key in ("width", "height"):
            if value := stream.get(key):
                metadata[key] = int(value)
        if duration := stream.get("duration") or probe_data.get("format", {}).get(
            "duration"
        ):
            try:
                metadata["duration"] = int(float(duration))
            except ValueError:
                pass
        return metadata

    @classmethod
    async def make_slideshow_from_web(
        cls, images_urls: list[str], audio_url: str | None
    ) -> bytes:
        cache_dir = CacheDir()
        try:
            output_path = cache_dir.get_file_path("slideshow.mp4")
            await wait_for_completion(
                cls.make_slideshow_file_from_web(images_urls, audio_url, output_path)
            )
            return await wait_for_completion(
                asyncio.to_thread(Path(output_path).read_bytes)
            )
        finally:
            await wait_for_completion(asyncio.to_thread(cache_dir.delete))

    @classmethod
    async def make_slideshow_file_from_web(
        cls, images_urls: list[str], audio_url: str | None, output_path: str
    ) -> None:
        """Write into a caller-owned directory, kept alive for the later upload."""
        work_dir = str(Path(output_path).parent)
        await cls.download_and_prepare_images(images_urls, work_dir)
        if audio_url:
            await cls.download_and_prepare_audio(audio_url, work_dir)

        command = cls._build_slideshow_command(
            images_input=f"{work_dir}/*.jpg",
            audio_input=f"{work_dir}/audio.m4a" if audio_url else None,
            output_path=output_path,
        )

        await cls._run_command(command)

    @classmethod
    async def download_and_prepare_images(
        cls, images_url: list[str], work_dir_path: str
    ) -> None:
        for n, url in enumerate(images_url):
            command = cls._build_command(
                inputs=[
                    url,
                ],
                output=f"{work_dir_path}/{n + 1:03d}.jpg",
                props=cls.__resize_image_options,
            )
            await cls._run_command(command)

        if len(images_url) == 1:
            shutil.copy(f"{work_dir_path}/001.jpg", f"{work_dir_path}/002.jpg")
            shutil.copy(f"{work_dir_path}/002.jpg", f"{work_dir_path}/003.jpg")

        if len(images_url) == 2:
            shutil.copy(f"{work_dir_path}/002.jpg", f"{work_dir_path}/003.jpg")

    @classmethod
    async def download_and_prepare_audio(
        cls, audio_url: str, work_dir_path: str
    ) -> None:
        command = cls._build_command(
            inputs=[audio_url],
            output=f"{work_dir_path}/audio.m4a",
            props=["-vn"],
        )
        await cls._run_command(command)

    @classmethod
    async def _run_command(cls, command: list[str], **kwargs: Any) -> CompletedProcess:
        kwargs.setdefault("stdin", subprocess.DEVNULL)
        async with cls._semaphore:
            return await async_wrap(subprocess.run)(command, check=True, **kwargs)

    @classmethod
    def _build_command(cls, inputs: list, output: str, props: list) -> list[str]:
        command = ["ffmpeg", "-y"]
        for input in inputs:
            command += ["-i", input]
        return (
            command
            + props
            + [
                output,
            ]
        )

    @classmethod
    def _build_slideshow_command(
        cls, images_input: str, audio_input: str | None, output_path: str
    ) -> list[str]:
        command = ["ffmpeg", "-y", "-framerate", "1/3"]
        command += ["-pattern_type", "glob", "-i", images_input]

        if audio_input:
            command += ["-stream_loop", "-1", "-i", audio_input]
            command += cls.__make_slideshow_options
        else:
            opts = cls.__make_slideshow_options.copy()
            opts.remove("-shortest")
            command += opts

        command += [
            output_path,
        ]
        return command
