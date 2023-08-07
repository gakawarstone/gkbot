from ._base import BaseExtractor


class SourceInfoExtractFailed(Exception):
    def __init__(self, source: BaseExtractor):
        self.sourse = source

    def __str__(self) -> str:
        return f'TikTok info extraction failed from source: {self.sourse}'
