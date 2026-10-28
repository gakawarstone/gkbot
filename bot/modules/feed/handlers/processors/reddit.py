from html import escape
from urllib.parse import urlparse

from aiogram.types import BufferedInputFile
from bs4 import BeautifulSoup, Tag

from services.gkfeed import FeedItem
from services.http import HttpRequestError, HttpService
from services.open_graph import OpenGraphService
from services.telegraph import HtmlToTelegraphContentConverter, TelegraphAPI

from ...ui.keyboards import FeedMarkup
from ...ui.keyboards.reddit import RedditFeedItemMarkup
from .registry import FeedProcessor
from .rendering import FeedRendering
from .video import send_video

_REDDIT_PREVIEW_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Twitterbot/1.0)",
}
_REDDIT_BASE_URL = "https://libreddit.qwik.space/"


def create_reddit_processor(rendering: FeedRendering) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        if await _send_reddit_preview(rendering, item):
            return

        url = _REDDIT_BASE_URL + "r/" + item.link.split("r/")[-1]
        soup = BeautifulSoup(await HttpService.get(url), "html.parser")
        title_tag = soup.find("title")
        title = title_tag.text.strip() if title_tag else "No title"

        if not soup.find_all(class_="post"):
            return await rendering.send_item(item)
        if image_url := _find_post_image_url(soup):
            return await rendering.send_photo(item, image_url, title)
        if video_url := _find_post_video_url(soup):
            return await send_video(rendering, item, video_url)
        if link := _find_post_link(soup):
            await rendering.answer(
                title.split("-")[0].strip()
                + f'\n\n<a href="{item.link}">{title.split("-")[-1].strip()}</a>',
                reply_markup=RedditFeedItemMarkup.get_item_markup(
                    item.id, link, "Ссылка"
                ),
                disable_web_page_preview=True,
            )
            return

        post_content = soup.find(class_="post_body")
        if post_content:
            gallery = soup.find(class_="gallery")
            if gallery:
                post_content = gallery
        if not isinstance(post_content, Tag):
            post_content = BeautifulSoup("", "html.parser")
        telegraph_url = await TelegraphAPI.create_telegraph_page(
            title=title.split("-")[0].strip(),
            content=HtmlToTelegraphContentConverter(_REDDIT_BASE_URL).convert(
                post_content
            ),
        )
        await rendering.answer(
            f'<b>{title.split("-")[0]}</b>\n\n<a href="{item.link}">{title.split("-")[-1].strip()}</a>',
            reply_markup=RedditFeedItemMarkup.get_item_markup(item.id, telegraph_url),
            disable_web_page_preview=True,
        )

    return FeedProcessor(
        "reddit",
        lambda item: item.link.startswith(("https://www.reddit.com",)),
        process,
    )


async def _send_reddit_preview(rendering: FeedRendering, item: FeedItem) -> bool:
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

    await rendering.answer_photo(
        BufferedInputFile(image_data, filename="reddit.jpg"),
        caption=(
            f'<a href="{escape(item.link, quote=True)}">'
            f"{escape(_get_subreddit_caption(item.link))}</a>"
        ),
        reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
    )
    return True


def _get_subreddit_caption(link: str) -> str:
    path_parts = urlparse(link).path.strip("/").split("/")
    for index, path_part in enumerate(path_parts[:-1]):
        if path_part.lower() == "r":
            return f"r/{path_parts[index + 1]}"
    return "Reddit"


def _find_post_image_url(soup: BeautifulSoup) -> str | None:
    post = soup.find(class_="post")

    if not post or not isinstance(post, Tag):
        return None

    images = post.find_all("image")
    if images:
        image = images[0]
        if isinstance(image, Tag) and image.get("href"):
            return _normalize_link(str(image.get("href")))

    imgs = post.find_all("img", attrs={"alt": "Post image"})
    if imgs:
        img = imgs[0]
        if isinstance(img, Tag) and img.get("src"):
            return _normalize_link(str(img.get("src")))

    return None


def _find_post_video_url(soup: BeautifulSoup) -> str | None:
    video = soup.find("meta", attrs={"property": "og:video"})
    if video and isinstance(video, Tag) and video.get("content"):
        return _normalize_link(str(video.get("content")))
    return None


def _find_post_link(soup: BeautifulSoup) -> str | None:
    post = soup.find(class_="post")

    if not post or not isinstance(post, Tag):
        return None

    links = post.find_all(id="post_url")
    if links:
        link = links[0]
        if isinstance(link, Tag) and link.get("href"):
            return _normalize_link(str(link.get("href")))
    return None


def _normalize_link(link: str) -> str:
    if not link.startswith("https"):
        return _REDDIT_BASE_URL + link
    return link
