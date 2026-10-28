from dataclasses import dataclass
from html import escape
from typing import Literal
from urllib.parse import urlparse

from aiogram.types import BufferedInputFile
from bs4 import BeautifulSoup, Tag

from services.feed_parser import FeedParser
from services.gkfeed import FeedItem
from services.http import HttpRequestError, HttpService
from services.open_graph import OpenGraphService
from services.telegraph import HtmlToTelegraphContentConverter, TelegraphAPI

from ...ui.keyboards import FeedMarkup
from ...ui.keyboards.reddit import RedditFeedItemMarkup
from . import BaseFeedItemView
from .video import VideoFeedItemView

_REDDIT_PREVIEW_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Twitterbot/1.0)",
}


@dataclass(frozen=True)
class _RedditPost:
    title: str
    kind: Literal["image", "video", "link", "telegraph"]
    content: str


class RedditFeedItemView(VideoFeedItemView, BaseFeedItemView):
    _base_url = "https://libreddit.qwik.space/"

    async def _process_reddit_item(self, item: FeedItem) -> None:
        if await self._send_reddit_preview(item):
            return

        url = self._base_url + "r/" + item.link.split("r/")[-1]
        html = await HttpService.get(url)
        post = await FeedParser.run(RedditFeedItemView._parse_post, html)
        if post is None:
            return await self._send_item(item)

        if post.kind == "image":
            return await self._send_photo(item, post.content, post.title)
        if post.kind == "video":
            return await self._send_video(item, post.content)
        if post.kind == "link":
            return await self._send_link_response(post.title, post.content, item)
        try:
            await self._send_telegraph_response(post.title, item, post.content)
        except Exception:  # noqa: BLE001 - Preserve the plain-link fallback.
            await self._send_item(item)

    @classmethod
    def _parse_post(cls, html: bytes) -> _RedditPost | None:
        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.find("title")
        title = title_tag.text.strip() if title_tag else "No title"
        if not soup.find_all(class_="post"):
            return None
        if image_url := cls._find_post_image_url(soup):
            return _RedditPost(title, "image", image_url)
        if video_url := cls._find_post_video_url(soup):
            return _RedditPost(title, "video", video_url)
        if link := cls._find_post_link(soup):
            return _RedditPost(title, "link", link)
        post_content = cls._get_post_content(soup)
        if post_content is None:
            post_content = BeautifulSoup("", "html.parser")
        content = HtmlToTelegraphContentConverter(cls._base_url).convert(post_content)
        return _RedditPost(title, "telegraph", content)

    async def _send_reddit_preview(self, item: FeedItem) -> bool:
        try:
            metadata = await OpenGraphService.get(
                item.link,
                headers=_REDDIT_PREVIEW_HEADERS,
            )
            if metadata.image_url is None:
                return False

            image_data = await HttpService.get(
                metadata.image_url,
                headers=_REDDIT_PREVIEW_HEADERS,
            )
        except HttpRequestError:
            return False

        await self.answer_photo(
            BufferedInputFile(image_data, filename="reddit.jpg"),
            caption=(
                f'<a href="{escape(item.link, quote=True)}">'
                f"{escape(self._get_subreddit_caption(item.link))}</a>"
            ),
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )
        return True

    @staticmethod
    def _get_subreddit_caption(link: str) -> str:
        path_parts = urlparse(link).path.strip("/").split("/")
        for index, path_part in enumerate(path_parts[:-1]):
            if path_part.lower() == "r":
                return f"r/{path_parts[index + 1]}"
        return "Reddit"

    @classmethod
    def _find_post_image_url(cls, soup: BeautifulSoup) -> str | None:
        post = soup.find(class_="post")

        if not post or not isinstance(post, Tag):
            return None

        images = post.find_all("image")
        if images and len(images) > 0:
            image = images[0]
            if isinstance(image, Tag) and image.get("href"):
                return cls._normalize_link(str(image.get("href")))

        imgs = post.find_all("img", attrs={"alt": "Post image"})
        if imgs and len(imgs) > 0:
            img = imgs[0]
            if isinstance(img, Tag) and img.get("src"):
                return cls._normalize_link(str(img.get("src")))

        return None

    @classmethod
    def _find_post_video_url(cls, soup: BeautifulSoup) -> str | None:
        video = soup.find("meta", attrs={"property": "og:video"})
        if video and isinstance(video, Tag) and video.get("content"):
            return cls._normalize_link(str(video.get("content")))
        return None

    @classmethod
    def _find_post_link(cls, soup: BeautifulSoup) -> str | None:
        post = soup.find(class_="post")

        if not post or not isinstance(post, Tag):
            return None

        links = post.find_all(id="post_url")
        if links and len(links) > 0:
            link = links[0]
            if isinstance(link, Tag) and link.get("href"):
                return cls._normalize_link(str(link.get("href")))
        return None

    async def _send_link_response(self, title: str, link: str, item: FeedItem) -> None:
        _title = title.split("-")[0].strip()
        link_caption = title.split("-")[-1].strip()

        await self.answer(
            _title + f'\n\n<a href="{item.link}">{link_caption}</a>',
            reply_markup=RedditFeedItemMarkup.get_item_markup(item.id, link, "Ссылка"),
            disable_web_page_preview=True,
        )

    async def _send_telegraph_response(
        self, title: str, item: FeedItem, content: str
    ) -> None:
        telegraph_url = await TelegraphAPI.create_telegraph_page(
            title=title.split("-")[0].strip(), content=content
        )
        await self.answer(
            f'<b>{title.split("-")[0]}</b>\n\n<a href="{item.link}">{title.split("-")[-1].strip()}</a>',
            reply_markup=RedditFeedItemMarkup.get_item_markup(item.id, telegraph_url),
            disable_web_page_preview=True,
        )

    @classmethod
    def _normalize_link(cls, link: str) -> str:
        if not link.startswith("https"):
            return cls._base_url + link
        return link

    @staticmethod
    def _get_post_content(soup: BeautifulSoup) -> Tag | None:
        post_body = soup.find(class_="post_body")

        if not post_body:
            return None

        if soup.find(class_="gallery"):
            post_body = soup.find(class_="gallery")
        return post_body if isinstance(post_body, Tag) else None
