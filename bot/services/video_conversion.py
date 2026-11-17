from services.ffmpeg_runner import FfmpegRunner


class VideoConversionService:
    """Convert caller-owned video files for Telegram."""

    @staticmethod
    async def convert_video(input_path: str, output_path: str) -> None:
        probe = await FfmpegRunner.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name,pix_fmt",
                "-of",
                "csv=p=0",
                input_path,
            ],
            capture_output=True,
            text=True,
        )
        # Telegram-compatible H.264 needs no video re-encoding, even for long clips.
        video_options = (
            ["-c:v", "copy"]
            if probe.stdout.strip() == "h264,yuv420p"
            else [
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-threads",
                "1",
                "-pix_fmt",
                "yuv420p",
            ]
        )
        command = FfmpegRunner.build_command(
            inputs=[input_path],
            output=output_path,
            props=video_options + ["-c:a", "aac"],
        )
        await FfmpegRunner.run(command)
