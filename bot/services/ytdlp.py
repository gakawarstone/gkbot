from dataclasses import dataclass

import yt_dlp
from aiogram.types import BufferedInputFile, FSInputFile

from utils.async_wrapper import async_wrap
from services.cache_dir import CacheDir


@dataclass
class AudioFileInfo:
    input_file: BufferedInputFile | FSInputFile
    duration: int
    title: str


ydl_opts = {
    'format': 'ba',
    'external_downloader': 'aria2c',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'm4a',
    }]
}

vkdl_opts = {
    'format': 'url240',
    'external_downloader': 'aria2c',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'm4a',
    }]
}


class YtdlpDownloader:
    @classmethod
    async def download_audio(cls, url: str) -> AudioFileInfo:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)

        return AudioFileInfo(
            input_file=await cls.__get_input_file(url),
            duration=info['duration'],
            title=info['title']
        )

    @staticmethod
    def __get_opts(url: str, output_path: str) -> dict:
        opts = ydl_opts
        if url.startswith('https://vk.com'):
            opts = vkdl_opts
        opts['outtmpl'] = output_path
        return opts

    @classmethod
    @async_wrap
    def __get_input_file(cls, url: str) -> FSInputFile:
        cache_dir = CacheDir()
        output_path = f'{cache_dir.path}/video'
        opts = cls.__get_opts(url, output_path)

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download(url)

        return FSInputFile(output_path + '.m4a', 'audio.mp3')
