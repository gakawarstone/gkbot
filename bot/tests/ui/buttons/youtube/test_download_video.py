from ui.buttons.youtube.download_video import (
    YoutubeDownloadVideoButtonBuilder,
    YoutubeDownloadVideoButtonData,
    YoutubeDownloadVideoButtonCallbackData,
    YoutubeDownloadVideoButtonCallbackDataDeserializer,
)

from . import generate_yt_code


def _create_button():
    yt_video_code = generate_yt_code()
    return YoutubeDownloadVideoButtonBuilder.build(
        button_data=YoutubeDownloadVideoButtonData(),
        callback_data=YoutubeDownloadVideoButtonCallbackData(yt_video_code),
    )


def test_youtube_button_creation():
    _create_button()


def test_callback_deserialization():
    yt_video_code = generate_yt_code()
    expected_callback_data = YoutubeDownloadVideoButtonCallbackData(yt_video_code)

    btn = YoutubeDownloadVideoButtonBuilder.build(
        button_data=YoutubeDownloadVideoButtonData(),
        callback_data=YoutubeDownloadVideoButtonCallbackData(yt_video_code),
    )

    desirialized_callback_data = (
        YoutubeDownloadVideoButtonCallbackDataDeserializer.deserialize(
            btn.callback_data
        )
    )

    assert expected_callback_data == desirialized_callback_data


def test_not_constant_callback():
    btn1 = _create_button()
    btn2 = _create_button()

    assert btn1.callback_data != btn2.callback_data
