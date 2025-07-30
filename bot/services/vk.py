from bs4 import BeautifulSoup, Tag

from services.http import HttpService


class VKService:
    @classmethod
    async def try_to_extract_video_link_from_post(cls, link: str) -> str:
        if not link.startswith("https://vk.com/wall"):
            raise ValueError

        html = await HttpService.get(link)
        soup = BeautifulSoup(html, "html.parser")
        video_post = soup.find(class_="page_post_thumb_video")

        if not video_post or not isinstance(video_post, Tag):
            raise ValueError

        href = video_post.get("href")
        if not href or not isinstance(href, str):
            raise ValueError

        return "https://vk.com" + href.split("?")[0]
