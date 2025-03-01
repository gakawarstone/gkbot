from typing import Optional
from bs4 import BeautifulSoup, Tag

from services.gkfeed import FeedItem
from services.telegraph import TelegraphAPI, HtmlToTelegraphContentConverter
from extensions.handlers.message.http import HttpExtension
from ui.keyboards.feed import FeedMarkup
from ui.keyboards.feed.reddit import RedditFeedItemMarkup
from . import BaseFeedItemView
from .video import VideoFeedItemView


class RedditFeedItemView(VideoFeedItemView, BaseFeedItemView, HttpExtension):
    _base_url = "https://libreddit.qwik.space/"

    async def _process_reddit_item(self, item: FeedItem):
        url = self._base_url + "r/" + item.link.split("r/")[-1]
        soup = await self._get_soup(url)

        title = soup.find("title").text

        image_url = await self._find_post_image_url(soup)
        if image_url:
            await self._send_photo(item, image_url, title)
            return

        video_url = await self._find_post_video_url(soup)
        if video_url:
            await self._send_video(item, video_url)
            return

        link = self._find_post_link(soup)
        if link:
            await self.event.answer(
                title + f'\n\n<a href="{link}">Link</a>',
                reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
                disable_web_page_preview=True,
            )
            return

        telegraph_url = await TelegraphAPI.create_telegraph_page(
            title=title.split("-")[0].strip(),
            content=HtmlToTelegraphContentConverter(self._base_url).convert(
                self._get_post_content(soup)
            ),
        )

        await self.event.answer(
            f'<b>{title.split("-")[0]}</b>\n\n<a href="{item.link}">{title.split("-")[-1].strip()}</a>',
            reply_markup=RedditFeedItemMarkup.get_item_markup(item.id, telegraph_url),
            disable_web_page_preview=True,
        )

    async def _find_post_image_url(self, soup: BeautifulSoup) -> Optional[str]:
        post = soup.find(class_="post")
        images = post.find_all("image")
        if images:
            return self._normalize_link(images[0]["href"])

        imgs = post.find_all("img", attrs={"alt": "Post image"})
        if imgs:
            return self._normalize_link(imgs[0]["src"])

        return None

    async def _find_post_video_url(self, soup: BeautifulSoup) -> Optional[str]:
        video = soup.find("meta", attrs={"property": "og:video"})
        if video:
            return self._normalize_link(video["content"])
        return None

    def _find_post_link(self, soup: BeautifulSoup) -> Optional[str]:
        post = soup.find(class_="post")
        links = post.find_all(id="post_url")
        if links:
            return self._normalize_link(links[0]["href"])
        return None

    def _normalize_link(self, link: str) -> str:
        if not link.startswith("https"):
            return self._base_url + link
        return link

    def _get_post_content(self, soup: BeautifulSoup) -> Tag:
        post_body = soup.find(class_="post_body")
        if soup.find(class_="gallery"):
            post_body = soup.find(class_="gallery")
        return post_body
