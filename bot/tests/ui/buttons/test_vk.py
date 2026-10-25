import pytest

from ui.buttons.vk import VKDownloadButtonCallbackDataDeserializer


@pytest.mark.parametrize(
    "value, expected_url",
    [
        ("wall-123", "https://vk.com/wall-123"),
        ("video-123_456", "https://vk.com/video-123_456"),
        ("https://vkvideo.ru/video-123_456", "https://vk.com/video-123_456"),
        ("https://vk.cc/abc-123", "https://vk.cc/abc-123"),
    ],
)
def test_legacy_callback(value: str, expected_url: str) -> None:
    data = VKDownloadButtonCallbackDataDeserializer.deserialize(
        f"vkbtn:dlmp4:False:{value}"
    )

    assert data.reference.download_url == expected_url
