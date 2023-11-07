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
    "format": "ba",
    "external_downloader": "aria2c",
}

vkdl_opts = {
    "format": "url240",
    "external_downloader": "aria2c",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
        }
    ],
}


video_opts = {
    "format": "worst[ext=mp4]",
    "external_downloader": "aria2c",
}


class YtdlpDownloader:
    @classmethod
    async def download_audio(cls, url: str) -> AudioFileInfo:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)

        return AudioFileInfo(
            input_file=await cls.__download_audio_file(url),
            duration=info["duration"],
            title=info["title"],
        )

    @classmethod
    async def download_video(cls, url: str) -> FSInputFile:
        return await cls.__download_file(url, video_opts, "video.mp4")

    @classmethod
    async def __download_audio_file(cls, url: str) -> FSInputFile:
        opts = cls.__choose_opts(url)
        file = await cls.__download_file(url, opts, "audio.m4a")
        return file

    @classmethod
    @async_wrap
    def __download_file(cls, url: str, opts: dict, file_name: str) -> FSInputFile:
        output_path = cls.__prepare_path() + "/" + file_name
        opts["outtmpl"] = output_path

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download(url)

        if "postprocessors" in opts:
            output_path += "." + opts["postprocessors"][0]["preferredcodec"]

        return FSInputFile(output_path, file_name)

    @staticmethod
    def __choose_opts(url: str) -> dict:
        if url.startswith("https://vk.com"):
            return vkdl_opts
        return ydl_opts

    @staticmethod
    def __prepare_path() -> str:
        cache_dir = CacheDir()
        return cache_dir.path
