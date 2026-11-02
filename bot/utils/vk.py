import re
from urllib.parse import urlsplit

_IDENTIFIER_PATTERN = re.compile(r"(?:wall-\d+(?:_\d+)?|video-\d+_\d+)")
_URL_PATTERN = re.compile(r"https?://[^\s<>]+")


def reconstruct_vk_url(text: str) -> str:
    """Extract a supported VK URL from message text or a legacy button value."""
    value = text.strip()
    if _IDENTIFIER_PATTERN.fullmatch(value):
        return f"https://vk.com/{value}"

    for match in _URL_PATTERN.finditer(value):
        url = match.group().rstrip(".,!)]}")
        parsed = urlsplit(url)
        if parsed.scheme != "https":
            continue
        if parsed.netloc == "vk.cc" and re.fullmatch(r"/[\w-]+", parsed.path):
            return url
        identifier = parsed.path.removeprefix("/")
        if parsed.netloc in {"vk.com", "vkvideo.ru"} and _IDENTIFIER_PATTERN.fullmatch(
            identifier
        ):
            return f"https://vk.com/{identifier}"

    raise ValueError("Unsupported VK reference")


def get_vk_id(text: str) -> str:
    """Return the legacy button value for a supported VK link."""
    url = reconstruct_vk_url(text)
    parsed = urlsplit(url)
    return url if parsed.netloc == "vk.cc" else parsed.path.removeprefix("/")
