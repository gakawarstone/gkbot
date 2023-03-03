from ._base import BaseDownloader


class SourceDownloadFailed(Exception):
    def __init__(self, source: BaseDownloader):
        self.sourse = source

    def __str__(self) -> str:
        return f'TikTok download failed from source: {self.sourse}'
