import re
from dataclasses import dataclass
from enum import Enum
from urllib.parse import SplitResult, urlsplit

_IDENTIFIER_PATTERN = re.compile(r"(?:wall-\d+(?:_\d+)?|video-\d+_\d+)")
_SHORT_PATH_PATTERN = re.compile(r"/[\w-]+")
_URL_PATTERN = re.compile(r"https?://[^\s<>]+")


class VKReferenceKind(Enum):
    IDENTIFIER = "identifier"
    SHORT_URL = "short_url"


@dataclass(frozen=True)
class VKReference:
    """A VK media identifier or an unresolved short URL."""

    kind: VKReferenceKind
    value: str

    def __post_init__(self) -> None:
        if self.kind is VKReferenceKind.IDENTIFIER:
            if _IDENTIFIER_PATTERN.fullmatch(self.value):
                return
        elif self.kind is VKReferenceKind.SHORT_URL and _is_short_url(
            urlsplit(self.value)
        ):
            return
        raise ValueError("Invalid VK reference")

    @property
    def download_url(self) -> str:
        if self.kind is VKReferenceKind.SHORT_URL:
            return self.value
        return f"https://vk.com/{self.value}"


def _is_short_url(parsed: SplitResult) -> bool:
    return (
        parsed.scheme == "https"
        and parsed.netloc == "vk.cc"
        and _SHORT_PATH_PATTERN.fullmatch(parsed.path) is not None
    )


def parse_vk_reference(text: str) -> VKReference:
    """Parse a supported identifier, URL, or link embedded in message text.

    Full media URLs are normalized to identifiers. Short URLs stay unresolved
    and keep their query string and fragment. Unsupported input raises ValueError.
    """
    value = text.strip()
    if _IDENTIFIER_PATTERN.fullmatch(value):
        return VKReference(VKReferenceKind.IDENTIFIER, value)

    for match in _URL_PATTERN.finditer(value):
        url = match.group().rstrip(".,!)]}")
        parsed = urlsplit(url)
        if _is_short_url(parsed):
            return VKReference(VKReferenceKind.SHORT_URL, url)
        if parsed.scheme != "https" or parsed.netloc not in {"vk.com", "vkvideo.ru"}:
            continue
        identifier = parsed.path.removeprefix("/")
        if _IDENTIFIER_PATTERN.fullmatch(identifier):
            return VKReference(VKReferenceKind.IDENTIFIER, identifier)

    raise ValueError("Unsupported VK reference")


def get_vk_id(url: str) -> str:
    """Compatibility adapter returning the value used by legacy VK buttons."""
    return parse_vk_reference(url).value


def reconstruct_vk_url(vk_id: str) -> str:
    """Compatibility adapter for identifiers and URLs stored in legacy buttons."""
    return parse_vk_reference(vk_id).download_url
