import re
from html import escape

from aiogram.utils.formatting import Bold, Code, Pre, Text
from aiogram.utils.text_decorations import HtmlDecoration

from .base import BaseHandler

_MARKDOWN_PATTERN = re.compile(
    r"```(?:(?P<language>\w*)[ \t]*\r?\n)?(?P<block>[\s\S]*?)```"
    r"|`(?P<inline>[^`]+)`"
    r"|\*\*(?P<bold>[^*]+)\*\*"
)


def parse_markdown(markdown_string: str) -> Text:
    """Parse supported Markdown once, keeping model text out of HTML markup."""
    nodes: list[str | Text] = []
    position = 0
    for match in _MARKDOWN_PATTERN.finditer(markdown_string):
        nodes.append(_render_list_markers(markdown_string[position : match.start()]))
        if match.group("block") is not None:
            code = match.group("block")
            nodes.append(Pre(code, language=match.group("language") or ""))
        elif match.group("inline") is not None:
            nodes.append(Code(match.group("inline")))
        else:
            nodes.append(Bold(_render_list_markers(match.group("bold"))))
        position = match.end()
    nodes.append(_render_list_markers(markdown_string[position:]))
    return Text(*nodes)


def _render_list_markers(text: str) -> str:
    return text.replace(" * ", "👉 ").replace("\n* ", "\n📌 ")


class _TelegramHTMLDecoration(HtmlDecoration):
    def pre_language(self, value: str, language: str) -> str:
        # aiogram 3.26 uses a language attribute; Telegram requires class.
        return f'<pre><code class="language-{escape(language, quote=True)}">{value}</code></pre>'


def render_html(text: Text) -> str:
    value, entities = text.render()
    return _TelegramHTMLDecoration().unparse(value, entities)


class MarkdownRenderHandlerExtension(BaseHandler):
    def _render_markdown(self, markdown_string: str) -> str:
        return render_html(parse_markdown(markdown_string))
