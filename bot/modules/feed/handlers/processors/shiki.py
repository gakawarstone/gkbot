from bs4 import BeautifulSoup, Tag

from services.gkfeed import FeedItem

from .._exceptions import FeedMediaExtractionError
from ._simple_rendering import SendPhoto, get_html_soup
from .matching import matches_source_url
from .registry import FeedProcessor


def create_shiki_processor(send_photo: SendPhoto) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        soup = await get_html_soup(item.link)
        media_url = _get_media_url(soup)
        title_name = _get_title_name(soup)
        await send_photo(item, media_url, item.text, title_name)

    return FeedProcessor(
        "shiki",
        lambda item: matches_source_url(
            item, frozenset({"shikimori.one", "shikimori.me", "shikimori.org"})
        ),
        process,
    )


def _get_media_url(soup: BeautifulSoup) -> str:
    poster_img = soup.select_one(".b-db_entry-poster picture img")
    if isinstance(poster_img, Tag):
        src = poster_img.get("src")
        if isinstance(src, str) and src.strip():
            return _normalize_media_url(src)

    poster_meta = soup.find("meta", attrs={"itemprop": "image"})
    if isinstance(poster_meta, Tag):
        content = poster_meta.get("content")
        if isinstance(content, str) and content.strip():
            return _normalize_media_url(content)

    picture_tag = soup.find("picture")
    if isinstance(picture_tag, Tag):
        source_tag = picture_tag.source
        if isinstance(source_tag, Tag):
            srcset = source_tag.get("srcset")
            if isinstance(srcset, list):
                srcset = srcset[0]

            if isinstance(srcset, str) and srcset.strip():
                candidates = srcset.rsplit(",", maxsplit=1)
                media_url = candidates[-1].strip().split()[0]
                return _normalize_media_url(media_url)

    meta_tag = soup.find("meta", attrs={"property": "og:image"})
    if isinstance(meta_tag, Tag):
        content = meta_tag.get("content")
        if isinstance(content, str) and content.strip():
            return _normalize_media_url(content)

    raise FeedMediaExtractionError("media url not found")


def _normalize_media_url(url: str) -> str:
    media_url = url.strip()
    if media_url.startswith("//"):
        return f"https:{media_url}"
    return media_url


def _get_title_name(soup: BeautifulSoup) -> str:
    h1_tag = soup.find("h1")
    if not isinstance(h1_tag, Tag):
        raise FeedMediaExtractionError("h1 tag not found")

    title = h1_tag.get_text(" ", strip=True).partition("/")[0].strip()
    if not title:
        raise FeedMediaExtractionError("title name not found")
    return title
