from dataclasses import dataclass
import os

import yt_dlp
from aiogram.types import BufferedInputFile, FSInputFile


@dataclass
class AudioFileInfo:
    input_file: BufferedInputFile | FSInputFile
    duration: int
    title: str


ydl_opts = {
    'format': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
    'outtmpl': 'video',
    # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
    'postprocessors': [{  # Extract audio using ffmpeg
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'm4a',
    }]
}


class YtdlpDownloader:
    @classmethod
    async def download_audio(cls, url: str) -> AudioFileInfo:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        return AudioFileInfo(
            input_file=await cls.__get_input_file(url),
            duration=info['duration'],
            title=info['title']
        )

    @classmethod  # FIXME: isnt async (!threadpoll because of race)
    async def __get_input_file(cls, url: str) -> FSInputFile:
        if os.path.isfile('video.m4a'):
            os.remove('video.m4a')

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(url)

        return FSInputFile('video.m4a', 'audio.mp3')