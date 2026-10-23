import pytest

from ui.buttons.download import DownloadAction
from ui.buttons.youtube.download import (
    YoutubeDownloadButtonBuilder,
    YoutubeDownloadButtonCallbackData,
)


@pytest.mark.parametrize("action", list(DownloadAction))
@pytest.mark.parametrize("status", [False, True])
def test_button_roundtrip(action: DownloadAction, status: bool) -> None:
    data = YoutubeDownloadButtonCallbackData(
        action=action,
        use_callback_message_as_status=status,
        yt_video_code="000opaque_id",
    )
    button = YoutubeDownloadButtonBuilder.build(data)
    assert button.callback_data is not None
    assert button.callback_data == f"ytbtn:{action.value}:{int(status)}:000opaque_id"
    assert button.text == action.label
    assert YoutubeDownloadButtonCallbackData.unpack(button.callback_data) == data


def test_different_targets_have_different_callbacks() -> None:
    def build(code: str) -> str:
        return YoutubeDownloadButtonCallbackData(
            action=DownloadAction.video,
            use_callback_message_as_status=False,
            yt_video_code=code,
        ).pack()

    assert build("first") != build("second")
