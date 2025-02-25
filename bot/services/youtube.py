from dataclasses import dataclass

from configs.env import YOUTUBE_API_KEY
from services.http import HttpService


@dataclass
class YoutubeVideoData:
    title: str
    channel_title: str
    thumbnail_url: str


class YoutubeApiService:
    @classmethod
    async def get_video_data(cls, url: str) -> YoutubeVideoData:
        video_code = url.split("=")[-1]
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_code}&key={YOUTUBE_API_KEY}"
        data = await HttpService.get_json(url)

        thumbnail_url = f"https://i3.ytimg.com/vi/{video_code}/maxresdefault.jpg"
        title = data["items"][0]["snippet"]["title"]
        channel_title = data["items"][0]["snippet"]["channelTitle"]

        return YoutubeVideoData(
            title=title, channel_title=channel_title, thumbnail_url=thumbnail_url
        )
