import asyncio
import subprocess
from subprocess import CompletedProcess
from typing import Any, ClassVar

from utils.async_wrapper import async_wrap


class FfmpegRunner:
    """Build argument lists and serialize FFmpeg/FFprobe subprocess calls."""

    _semaphore: ClassVar[asyncio.Semaphore] = asyncio.Semaphore(1)

    @staticmethod
    def build_command(inputs: list[str], output: str, props: list[str]) -> list[str]:
        command = ["ffmpeg", "-y"]
        for input_path in inputs:
            command.extend(["-i", input_path])
        return [*command, *props, output]

    @staticmethod
    def build_probe_command(input_path: str, props: list[str]) -> list[str]:
        return ["ffprobe", *props, input_path]

    @classmethod
    async def run(cls, command: list[str], **kwargs: Any) -> CompletedProcess:
        """Run off the event loop, preserving subprocess results and exceptions.

        FFmpeg and FFprobe share one process slot. Cancellation does not stop
        executor work; callers owning temporary files must wait before cleanup.
        """
        kwargs.setdefault("stdin", subprocess.DEVNULL)
        async with cls._semaphore:
            return await async_wrap(subprocess.run)(command, check=True, **kwargs)
