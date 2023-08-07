import subprocess

from services.cache_dir import CacheDir


class FfmpegService:
    __resize_image_options = [
        '-vf', (
            'scale=trunc(oh*a/2)*2:720,'
            'pad=max(iw\,ih*9/16):max(ih\,iw*16/9):(ow-iw)/2:(oh-ih)/2:black'
        ),
    ]
    __make_slideshow_options = [
        '-c:v', 'libx264',
        '-shortest',
        '-vf', 'scale=720:1080',
        '-r', '30',
        '-pix_fmt', 'yuv420p',
    ]

    @classmethod
    async def make_slideshow_from_web(
            cls, images_urls: list[str], audio_url: str
    ) -> bytes:
        cache_dir = CacheDir()

        await cls.download_and_prepare_images(images_urls, cache_dir.path)

        command = cls._build_slideshow_command(
            images_input=f'{cache_dir.path}/*.jpg',
            audio_input=audio_url,
            output_path=f'{cache_dir.path}/slideshow.mp4',
        )

        subprocess.run(command, check=True)
        content = open(f'{cache_dir.path}/slideshow.mp4', 'rb').read()
        cache_dir.delete()
        return content

    @classmethod
    async def download_and_prepare_images(
            cls, images_url: list[str], work_dir_path: str
    ) -> None:
        for n, url in enumerate(images_url):
            command = cls._build_command(
                inputs=[url,],
                output=f'{work_dir_path}/{n + 1}.jpg',
                props=cls.__resize_image_options
            )
            subprocess.run(command, check=True)

    @classmethod
    def _build_command(
            cls, inputs: list, output: str, props: list
    ) -> list[str]:
        command = ['ffmpeg', '-y']
        for input in inputs:
            command += ['-i', input]
        return command + props + [output,]

    @classmethod
    def _build_slideshow_command(
            cls, images_input: str, audio_input: str, output_path: str
    ) -> list[str]:
        command = ['ffmpeg', '-y', '-framerate', '1/3']
        command += ['-pattern_type', 'glob', '-i', images_input]
        command += ['-stream_loop', '-1', '-i', audio_input]
        command += cls.__make_slideshow_options
        command += [output_path,]
        return command
