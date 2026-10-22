from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._base import BaseExtractor


class SourceInfoExtractFailed(Exception):
    def __init__(self, source: "BaseExtractor") -> None:
        self.source = source
        super().__init__(source)

    def __str__(self) -> str:
        return f"TikTok info extraction failed from source: {self.source}"
