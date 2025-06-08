import re

from aiogram.utils.formatting import Bold
from .base import BaseHandler


class MarkdownRenderHandlerExtension(BaseHandler):
    # This function was generated with the assistance of deepseek-r1
    # It handles markdown to tg-html rendering including bold, inline code, and code blocks.
    def _render_markdown(self, markdown_string: str) -> str:
        bold_pattern = r"\*\*([^*]+)\*\*"
        code_pattern = r"```(\w*)\s*\n?([\s\S]*?)```"
        inline_code_pattern = r"`([^`]+)`"

        def replace_bold_func(match):
            text = match.group(1)
            return Bold(text).as_html()

        def replace_code_func(match: re.Match) -> str:
            language = match.group(1) or ""
            code = match.group(2)

            if not language:
                if code.startswith(("\n", "\r")):
                    code = code[1:]
                if code.endswith(("\n", "\r")):
                    code = code[:-1]

            code_escaped = (
                code.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("*", "&#42;")  # Prevent accidental bold processing
            )
            return f'<pre><code class="language-{language}">{code_escaped}</code></pre>'

        def replace_inline_code_func(match):
            code = match.group(1)
            code_escaped = (
                code.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("*", "&#42;")  # Prevent accidental bold processing
            )
            return f"<code>{code_escaped}</code>"

        result = re.sub(code_pattern, replace_code_func, markdown_string)
        result = re.sub(inline_code_pattern, replace_inline_code_func, result)
        result = re.sub(bold_pattern, replace_bold_func, result)
        result = result.replace(" * ", "👉 ")
        result = result.replace("\n* ", "\n📌 ")

        return result
