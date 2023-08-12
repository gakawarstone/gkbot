class SerializationError(Exception):
    'failed to serialize'


class TikTokVideoUrlExtractionFailed(Exception):
    def __init__(self, url: str) -> None:
        self.url = url

    def __str__(self) -> str:
        return f'TikTok video url extraction failed {self.url}'


class TikTokInvalidUrl(Exception):
    def __init__(self, url: str) -> None:
        self.url = url

    def __str__(self) -> str:
        return f'Invalid TikTok video url {self.url}'


class TikTokInfoExtractionFailed(Exception):
    def __init__(self, url: str) -> None:
        self.url = url

    def __str__(self) -> str:
        return f'Download failed from url {self.url}'
