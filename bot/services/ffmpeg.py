import asyncio
import shutil
from pathlib import Path

from services.audio import AudioService
from services.cache_dir import CacheDir
from services.ffmpeg_runner import FfmpegRunner
from utils.async_cleanup import wait_for_completion


class FfmpegService:
    SLIDESHOW_WIDTH = 720
    SLIDESHOW_HEIGHT = 1080

    __resize_image_options = [
        "-vf",
        (
            "scale=trunc(oh*a/2)*2:720,"
            "pad=max(iw\\,ih*9/16):max(ih\\,iw*16/9):(ow-iw)/2:(oh-ih)/2:black"
        ),
    ]
    __make_slideshow_options = [
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
            await AudioService.download_and_prepare_audio(audio_url, work_dir)

        command = cls._build_slideshow_command(
            images_input=f"{work_dir}/*.jpg",
            audio_input=f"{work_dir}/audio.m4a" if audio_url else None,
            output_path=output_path,
        )

        await FfmpegRunner.run(command)

    @classmethod
    async def download_and_prepare_images(
        cls, images_url: list[str], work_dir_path: str
    ) -> None:
        for n, url in enumerate(images_url):
            command = FfmpegRunner.build_command(
                inputs=[
                    url,
                ],
                output=f"{work_dir_path}/{n + 1:03d}.jpg",
                props=cls.__resize_image_options,
            )
            await FfmpegRunner.run(command)

        if len(images_url) == 1:
            shutil.copy(f"{work_dir_path}/001.jpg", f"{work_dir_path}/002.jpg")
            shutil.copy(f"{work_dir_path}/002.jpg", f"{work_dir_path}/003.jpg")

        if len(images_url) == 2:
            shutil.copy(f"{work_dir_path}/002.jpg", f"{work_dir_path}/003.jpg")

    @classmethod
    def _build_slideshow_command(
        cls, images_input: str, audio_input: str | None, output_path: str
    ) -> list[str]:
        command = ["-framerate", "1/3"]
        command += ["-pattern_type", "glob", "-i", images_input]

        if audio_input:
            command += ["-stream_loop", "-1", "-i", audio_input]
            command += cls.__make_slideshow_options
        else:
            opts = cls.__make_slideshow_options.copy()
            opts.remove("-shortest")
            command += opts

        return FfmpegRunner.build_command(inputs=[], output=output_path, props=command)
