from typing import Any

from .base import BaseComponent


class BaseCreatorComponent(BaseComponent):
    def __init__(self) -> None:
        self._has_highlighted_property: bool

    def _render_property(
        self, prop: Any, prefix: str = "", new_line: bool = True
    ) -> str:
        highlight = (
            self._is_property_not_exist(prop) and not self._has_highlighted_property
        )
        text = self._highlight_if(
            highlight, prefix + self._render_if_exist(prop, "... ")
        )
        if new_line:
            text += "\n"

        if highlight:
            self._has_highlighted_property = True

        return text
