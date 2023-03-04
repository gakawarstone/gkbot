from dataclasses import dataclass
import os

import yt_dlp
from aiogram.types import BufferedInputFile, FSInputFile
from pytube import YouTube as PyTube  # FIXME: theris ytinfo dependenci


@dataclass
class YouTubeAudio:
    input_file: BufferedInputFile | FSInputFile
    duration: int
    title: str


ydl_opts = {
    'format': 'm4a/bestaudio/best',
    'outtmpl': 'video',
    # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
    'postprocessors': [{  # Extract audio using ffmpeg
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'm4a',
    }]
}


class YouTubeDownloader:
    @classmethod
    async def download_audio(cls, url: str) -> YouTubeAudio:
        info = PyTube(url)

        duration = 0
        if info.length:
            duration = info.length

        return YouTubeAudio(
            input_file=await cls.__get_input_file(info),
            duration=duration,
            title=info.title
        )

    @classmethod  # FIXME: isnt async (!threadpoll because of race)
    async def __get_input_file(cls, info: PyTube) -> FSInputFile:
        if os.path.isfile('video.m4a'):
            os.remove('video.m4a')

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(info.watch_url)

        return FSInputFile('video.m4a', 'audio.mp3')
