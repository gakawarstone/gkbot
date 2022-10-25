import asyncio
from dataclasses import dataclass
from io import BytesIO

from aiogram.types import BufferedInputFile
from pytube import YouTube as PyTube


@dataclass
class YouTubeAudio:
    input_file: BufferedInputFile
    duration: int
    title: str


class YouTubeDownloader:
    @classmethod
    async def download_audio(cls, url: str) -> YouTubeAudio:
        info = PyTube(url)
        return YouTubeAudio(
            input_file=await cls.__get_input_file(info),
            duration=info.length,
            title=info.title
        )

    @classmethod
    async def __get_input_file(cls, info: PyTube) -> BufferedInputFile:
        audio = info.streams.get_audio_only()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, audio.stream_to_buffer, buffer := BytesIO())
        return BufferedInputFile(buffer.getvalue(), 'audio.mp3')
