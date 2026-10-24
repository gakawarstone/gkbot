import pytest

from utils.vk import (
    VKReference,
    VKReferenceKind,
    parse_vk_reference,
)


@pytest.mark.parametrize(
    "identifier",
    ["wall-50883936", "wall-50883936_456244451", "video-50883936_456244451"],
)
def test_identifiers(identifier: str) -> None:
    reference = parse_vk_reference(identifier)

    assert reference == VKReference(VKReferenceKind.IDENTIFIER, identifier)
    assert reference.download_url == f"https://vk.com/{identifier}"


@pytest.mark.parametrize("host", ["vk.com", "vkvideo.ru"])
@pytest.mark.parametrize("identifier", ["wall-123_456", "wall-123", "video-123_456"])
def test_full_urls(host: str, identifier: str) -> None:
    reference = parse_vk_reference(f"https://{host}/{identifier}?list=abc#section")

    assert reference.kind is VKReferenceKind.IDENTIFIER
    assert reference.value == identifier
    assert reference.download_url == f"https://vk.com/{identifier}"


@pytest.mark.parametrize(
    "url",
    [
        "https://vk.cc/abc-123",
        "https://vk.cc/video-123_456",
        "https://vk.cc/abc?ref=share#section",
    ],
)
def test_short_urls_remain_unresolved(url: str) -> None:
    reference = parse_vk_reference(url)

    assert reference == VKReference(VKReferenceKind.SHORT_URL, url)
    assert reference.download_url == url


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Смотри https://vk.com/video-123_456 здесь", "video-123_456"),
        ("Смотри (https://vk.cc/abc-123).", "https://vk.cc/abc-123"),
        ("  wall-123_456  ", "wall-123_456"),
    ],
)
def test_message_text(text: str, expected: str) -> None:
    assert parse_vk_reference(text).value == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "other",
        "video-123",
        "wall-123_invalid",
        "https://vk.com/other",
        "http://vk.com/video-123_456",
        "https://example.com/video-123_456",
        "https://vk.com.evil.test/video-123_456",
        "https://user@vk.com/video-123_456",
        "https://vk.cc/",
        "https://vk.cc/abc/other",
        "https://example.com/?url=https://vk.com/video-123_456",
        "unsupported video-123_456 text",
    ],
)
def test_unsupported_references(value: str) -> None:
    with pytest.raises(ValueError, match="Unsupported VK reference"):
        parse_vk_reference(value)


@pytest.mark.parametrize(
    "kind, value",
    [
        (VKReferenceKind.IDENTIFIER, "https://vk.cc/abc"),
        (VKReferenceKind.SHORT_URL, "video-123_456"),
        (VKReferenceKind.IDENTIFIER, "other"),
        (VKReferenceKind.SHORT_URL, "https://example.com/abc"),
    ],
)
def test_invalid_reference_state(kind: VKReferenceKind, value: str) -> None:
    with pytest.raises(ValueError, match="Invalid VK reference"):
        VKReference(kind, value)
