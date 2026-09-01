import asyncio
import json
import re
from typing import ClassVar

import aiohttp
from aiogram.types import BufferedInputFile, InputMediaPhoto
from bs4 import BeautifulSoup, Tag


class InstagramDownloadError(Exception):
    """An Instagram post could not be extracted or downloaded."""


class InstagramService:
    _headers: ClassVar[dict[str, str]] = {"User-Agent": "Mozilla/5.0"}
    _post_shortcode_pattern = re.compile(r"/p/([^/?#]+)")

    @classmethod
    async def get_photos_album(cls, url: str) -> list[InputMediaPhoto]:
        try:
            links = await cls._extract_photo_links(url)
            photos = await cls._download_photos(links, referer=url)
        except (aiohttp.ClientError, json.JSONDecodeError, TimeoutError) as error:
            raise InstagramDownloadError(url) from error

        return [InputMediaPhoto(media=photo) for photo in photos]

    @classmethod
    async def _extract_photo_links(cls, url: str) -> list[str]:
        shortcode_match = cls._post_shortcode_pattern.search(url)
        if shortcode_match is None:
            raise InstagramDownloadError(url)

        embed_url = (
            f"https://www.instagram.com/p/{shortcode_match.group(1)}/embed/captioned/"
        )
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(
            headers=cls._headers, timeout=timeout
        ) as session, session.get(embed_url) as response:
            response.raise_for_status()
            html = await response.text()

        post = cls._extract_post_data(html, shortcode_match.group(1))
        sidecar = post.get("edge_sidecar_to_children")
        nodes: list[dict[str, object]] = []
        if isinstance(sidecar, dict) and isinstance(sidecar.get("edges"), list):
            for edge in sidecar["edges"]:
                if not isinstance(edge, dict):
                    continue
                node = edge.get("node")
                if isinstance(node, dict):
                    nodes.append(node)
        else:
            nodes = [post]

        links = [
            display_url
            for node in nodes
            if not node.get("is_video")
            and isinstance(display_url := node.get("display_url"), str)
        ]
        if not links:
            raise InstagramDownloadError(url)
        return links

    @classmethod
    def _extract_post_data(cls, html: str, shortcode: str) -> dict[str, object]:
        soup = BeautifulSoup(html, "html.parser")
        for script in soup.find_all("script"):
            if not isinstance(script, Tag):
                continue
            script_text = script.string or script.get_text()
            if "contextJSON" not in script_text or shortcode not in script_text:
                continue

            server_data = cls._extract_server_data(script_text)
            for context_json in cls._find_values(server_data, "contextJSON"):
                if not isinstance(context_json, str):
                    continue
                context = json.loads(context_json)
                post = context.get("gql_data", {}).get("shortcode_media")
                if isinstance(post, dict) and post.get("shortcode") == shortcode:
                    return post

        raise InstagramDownloadError(shortcode)

    @staticmethod
    def _extract_server_data(script: str) -> object:
        marker = "s.handle("
        marker_index = script.find(marker)
        if marker_index < 0:
            raise InstagramDownloadError("Instagram embed data is missing")

        start = marker_index + len(marker)
        depth = 0
        in_string = False
        escaped = False
        for index, character in enumerate(script[start:], start=start):
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
                continue

            if character == '"':
                in_string = True
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(script[start : index + 1])

        raise InstagramDownloadError("Instagram embed data is incomplete")

    @classmethod
    def _find_values(cls, data: object, key: str) -> list[object]:
        values: list[object] = []
        if isinstance(data, dict):
            if key in data:
                values.append(data[key])
            for value in data.values():
                values.extend(cls._find_values(value, key))
        elif isinstance(data, list):
            for value in data:
                values.extend(cls._find_values(value, key))
        return values

    @classmethod
    async def _download_photos(
        cls, links: list[str], referer: str
    ) -> list[BufferedInputFile]:
        timeout = aiohttp.ClientTimeout(total=30)
        headers = {**cls._headers, "Referer": referer}
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            return await asyncio.gather(
                *(
                    cls._download_photo(session, link, index)
                    for index, link in enumerate(links, start=1)
                )
            )

    @staticmethod
    async def _download_photo(
        session: aiohttp.ClientSession, link: str, index: int
    ) -> BufferedInputFile:
        async with session.get(link) as response:
            response.raise_for_status()
            content = await response.read()

        if not content:
            raise InstagramDownloadError(link)
        return BufferedInputFile(content, filename=f"instagram_{index}.jpg")
