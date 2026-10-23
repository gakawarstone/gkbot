from services.ffmpeg_runner import FfmpegRunner


class VideoConversionService:
    """Convert caller-owned video files to H.264/AAC MP4."""

    @staticmethod
    async def convert_video(input_path: str, output_path: str) -> None:
        command = FfmpegRunner.build_command(
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
        await FfmpegRunner.run(command)
