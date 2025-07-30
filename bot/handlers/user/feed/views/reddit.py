from typing import Optional
from bs4 import BeautifulSoup, Tag

from services.gkfeed import FeedItem
from services.telegraph import TelegraphAPI, HtmlToTelegraphContentConverter
from extensions.handlers.message.http import HttpExtension
from ui.keyboards.feed.reddit import RedditFeedItemMarkup
from . import BaseFeedItemView
from .video import VideoFeedItemView


class RedditFeedItemView(VideoFeedItemView, BaseFeedItemView, HttpExtension):
    _base_url = "https://libreddit.qwik.space/"

    async def _process_reddit_item(self, item: FeedItem):
        url = self._base_url + "r/" + item.link.split("r/")[-1]
        soup = await self._get_soup(url)
        title_tag = soup.find("title")
        title = title_tag.text.strip() if title_tag else "No title"

        if not soup.find_all(class_="post"):
            return await self._send_item(item)

        if image_url := self._find_post_image_url(soup):
            return await self._send_photo(item, image_url, title)

        if video_url := self._find_post_video_url(soup):
            return await self._send_video(item, video_url)

        if link := self._find_post_link(soup):
            return await self._send_link_response(title, link, item)
        try:
            await self._send_telegraph_response(title, item, soup)
        except Exception:
            await self._send_item(item)

    def _find_post_image_url(self, soup: BeautifulSoup) -> Optional[str]:
        post = soup.find(class_="post")

        if not post or not isinstance(post, Tag):
            return None

        images = post.find_all("image")
        if images and len(images) > 0:
            image = images[0]
            if isinstance(image, Tag) and image.get("href"):
                return self._normalize_link(str(image["href"]))

        imgs = post.find_all("img", attrs={"alt": "Post image"})
        if imgs and len(imgs) > 0:
            img = imgs[0]
            if isinstance(img, Tag) and img.get("src"):
                return self._normalize_link(str(img["src"]))

        return None

    def _find_post_video_url(self, soup: BeautifulSoup) -> Optional[str]:
        video = soup.find("meta", attrs={"property": "og:video"})
        if video and isinstance(video, Tag) and video.get("content"):
            return self._normalize_link(str(video["content"]))
        return None

    def _find_post_link(self, soup: BeautifulSoup) -> Optional[str]:
        post = soup.find(class_="post")

        if not post or not isinstance(post, Tag):
            return None

        links = post.find_all(id="post_url")
        if links and len(links) > 0:
            link = links[0]
            if isinstance(link, Tag) and link.get("href"):
                return self._normalize_link(str(link["href"]))
        return None

    async def _send_link_response(self, title: str, link: str, item: FeedItem):
        _title = title.split("-")[0].strip()
        link_caption = title.split("-")[-1].strip()

        return await self.answer(
            _title + f'\n\n<a href="{item.link}">{link_caption}</a>',
            reply_markup=RedditFeedItemMarkup.get_item_markup(item.id, link, "Ссылка"),
            disable_web_page_preview=True,
        )

    async def _send_telegraph_response(
        self, title: str, item: FeedItem, soup: BeautifulSoup
    ):
        telegraph_url = await self._create_telegraph_page(title, soup)
        await self.answer(
            f'<b>{title.split("-")[0]}</b>\n\n<a href="{item.link}">{title.split("-")[-1].strip()}</a>',
            reply_markup=RedditFeedItemMarkup.get_item_markup(item.id, telegraph_url),
            disable_web_page_preview=True,
        )

    async def _create_telegraph_page(self, title: str, soup: BeautifulSoup) -> str:
        post_content = self._get_post_content(soup)
        if post_content is None:
            post_content = BeautifulSoup("", "html.parser")
        return await TelegraphAPI.create_telegraph_page(
            title=title.split("-")[0].strip(),
            content=HtmlToTelegraphContentConverter(self._base_url).convert(
                post_content
            ),
        )

    def _normalize_link(self, link: str) -> str:
        if not link.startswith("https"):
            return self._base_url + link
        return link

    def _get_post_content(self, soup: BeautifulSoup) -> Optional[Tag]:
        post_body = soup.find(class_="post_body")

        if not post_body:
            return None

        if soup.find(class_="gallery"):
            post_body = soup.find(class_="gallery")
        return post_body if isinstance(post_body, Tag) else None
