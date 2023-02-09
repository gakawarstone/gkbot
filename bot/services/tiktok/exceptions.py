class SerializationError(Exception):
    'failed to serialize'


class TikTokInvalidUrl(Exception):
    def __init__(self, url: str) -> None:
        self.url = url

    def __str__(self) -> str:
        return f'Invalid TikTok video url {self.url}'


class TikTokDownloadFailed(Exception):
    def __init__(self, url: str) -> None:
        self.url = url

    def __str__(self) -> str:
        return f'Download failed from url {self.url}'
