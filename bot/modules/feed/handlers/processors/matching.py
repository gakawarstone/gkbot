from urllib.parse import urlsplit

from services.gkfeed import FeedItem


def matches_source_url(
    item: FeedItem,
    hosts: frozenset[str] = frozenset(),
    *,
    scheme: str = "https",
    path_prefix: str = "",
    host_prefix: str | None = None,
) -> bool:
    """Match a source's authority and optional path, independent of URL text."""
    if any(character.isspace() or ord(character) < 32 for character in item.link):
        return False
    try:
        parsed = urlsplit(item.link)
        host = parsed.hostname
        port = parsed.port
    except ValueError:
        return False

    if (
        parsed.scheme != scheme
        or host is None
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443 if scheme == "https" else 80)
    ):
        return False

    host = host.removesuffix(".")
    matches_host = host in hosts or (
        host_prefix is not None and host.startswith(host_prefix)
    )
    return matches_host and parsed.path.startswith(path_prefix)
