import json
from typing import TypeAlias

from bs4 import BeautifulSoup, Tag, Comment
from bs4.element import NavigableString, PageElement

from configs.env import TELEGRAPH_API_KEY
from services.http import HttpService

_NODE = BeautifulSoup | Tag | NavigableString | Comment | PageElement
TelegraphContent: TypeAlias = str


class TelegraphAPI:
    @classmethod
    async def create_telegraph_page(
        cls,
        title: str,
        content: TelegraphContent,
        author_name: str = "GKBOT",
    ) -> str:
        params = {
            "access_token": TELEGRAPH_API_KEY,
            "title": title[:200],
            "author_name": author_name,
            "content": content,
            "return_content": False,
        }
        resp = await HttpService.post_json(
            "https://api.telegra.ph/createPage", body=params
        )
        return resp["result"]["url"]


class HtmlToTelegraphContentConverter:
    _allowed_tags = {
        "a",
        "aside",
        "b",
        "blockquote",
        "br",
        "code",
        "em",
        "figcaption",
        "figure",
        "h3",
        "h4",
        "hr",
        "i",
        "iframe",
        "img",
        "li",
        "ol",
        "p",
        "pre",
        "s",
        "strong",
        "u",
        "ul",
        "video",
    }
    _allowed_attrs = {"href", "src"}

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url

    def convert(self, soup: BeautifulSoup | Tag) -> TelegraphContent:
        root_nodes = []
        for child in soup.contents:
            root_nodes.extend(self.__process_node(child, True))
        return json.dumps(root_nodes)

    def __process_node(
        self, node: _NODE, preserve_whitespace: bool
    ) -> list[dict | str]:
        if isinstance(node, Comment):
            return []
        elif isinstance(node, NavigableString):
            text = str(node)
            if not preserve_whitespace:
                text = text.strip()
            return [text] if text else []
        elif isinstance(node, Tag) and node.name in self._allowed_tags:
            tag = node.name
            attrs: dict[str, str] = {}
            for attr in self._allowed_attrs:
                attr_val = node.get(attr)
                if not isinstance(attr_val, str):
                    continue
                if attr_val.startswith("/"):
                    attr_val = self._base_url + attr_val
                attrs[attr] = attr_val
            new_preserve = preserve_whitespace
            if tag in ["pre", "code"]:
                new_preserve = True
            children = []
            for child in node.contents:
                children.extend(self.__process_node(child, new_preserve))
            element: dict[str, str | dict[str, str] | list[dict | str]] = {"tag": tag}
            if attrs:
                element["attrs"] = attrs
            if children:
                element["children"] = children
            return [element]
        elif isinstance(node, Tag):
            children = []
            for child in node.contents:
                children.extend(self.__process_node(child, preserve_whitespace))
            return children
        else:
            return []
