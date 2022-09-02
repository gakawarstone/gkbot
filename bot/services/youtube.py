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
            duration=await info.length,
            title=await info.title
        )

    @classmethod
    async def __get_input_file(cls, info: PyTube) -> BufferedInputFile:
        streams = await info.streams
        audio = streams.get_audio_only()
        await audio.stream_to_buffer(buffer := BytesIO())
        return BufferedInputFile(buffer.getvalue(), 'audio.mp3')
