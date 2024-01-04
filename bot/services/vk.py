from bs4 import BeautifulSoup

from services.http import HttpService


class VKService:
    @classmethod
    async def try_to_extract_video_link_from_post(cls, link: str) -> str:
        if not link.startswith("https://vk.com/wall"):
            raise ValueError

        html = await HttpService.get(link)
        soup = BeautifulSoup(html, "html.parser")
        video_post = soup.find(class_="page_post_thumb_video")

        if not video_post:
            raise ValueError

        return "https://vk.com" + video_post["href"].split("?")[0]
