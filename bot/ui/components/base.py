from typing import Any


class BaseComponent:
    def _highlight_if(self, statement: bool, text: str) -> str:
        if not statement:
            return text
        return '<b>> ' + text + '</b>'

    def _is_property_not_exist(self, prop: Any) -> bool:
        return prop is None

    def _render_if_exist(self, prop: Any, text_else: str = '') -> str:
        if prop is not None:
            return prop + ' '
        return text_else
