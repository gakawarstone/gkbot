import pytest

from ui.buttons.vk import (
    VKDownloadButtonCallbackData,
    VKDownloadButtonCallbackDataDeserializer,
    VKDownloadButtonCallbackDataSerializer,
    VKDownloadButtonData,
)
from ui.keyboards.vk import VkMarkup
from utils.vk import parse_vk_reference


@pytest.mark.parametrize(
    "button", [VKDownloadButtonData.audio, VKDownloadButtonData.video]
)
@pytest.mark.parametrize("use_status", [False, True])
@pytest.mark.parametrize(
    "value", ["wall-123_456", "video-123_456", "https://vk.cc/abc-123"]
)
def test_callback_roundtrip(
    button: VKDownloadButtonData, use_status: bool, value: str
) -> None:
    data = VKDownloadButtonCallbackData(parse_vk_reference(value), use_status)

    payload = VKDownloadButtonCallbackDataSerializer.serialize(button, data)

    assert payload == f"vkbtn:{button.value.event}:{use_status}:{value}"
    assert VKDownloadButtonCallbackDataDeserializer.deserialize(payload) == data
    assert len(payload.encode()) <= 64


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
    assert data.use_callback_message_as_status is False


def test_unsupported_callback_reference() -> None:
    with pytest.raises(ValueError, match="Unsupported VK reference"):
        VKDownloadButtonCallbackDataDeserializer.deserialize(
            "vkbtn:dlmp4:False:https://example.com/other"
        )


def test_download_keyboard_uses_reference() -> None:
    reference = parse_vk_reference("https://vk.cc/abc-123")

    markup = VkMarkup.get_download_dialog(reference)

    for button in markup.inline_keyboard[0][:2]:
        assert button.callback_data is not None
        data = VKDownloadButtonCallbackDataDeserializer.deserialize(
            button.callback_data
        )
        assert data.reference == reference
        assert data.use_callback_message_as_status is True
