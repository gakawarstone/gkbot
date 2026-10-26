import json

from services.ffmpeg_runner import FfmpegRunner


class VideoMetadataService:
    """Read dimensions and whole-second duration from the first video stream."""

    @staticmethod
    async def get_video_metadata(input_path: str) -> dict[str, int]:
        command = FfmpegRunner.build_probe_command(
            input_path,
            props=[
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height,duration",
                "-of",
                "json",
            ],
        )
        result = await FfmpegRunner.run(command, capture_output=True, text=True)
        streams = json.loads(result.stdout).get("streams", [])
        if not streams:
            return {}

        stream = streams[0]
        metadata = {}
        for key in ("width", "height"):
            if value := stream.get(key):
                metadata[key] = int(value)
        if duration := stream.get("duration"):
            try:
                metadata["duration"] = int(float(duration))
            except ValueError:
                pass
        return metadata
