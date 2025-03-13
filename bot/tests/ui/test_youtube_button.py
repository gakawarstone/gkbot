import random

from ui.buttons.youtube import (
    YoutubeDownloadAudioButtonBuilder,
    YoutubeDownloadAudioButtonData,
    YoutubeDownloadAudioButtonCallbackData,
    YoutubeDownloadAudioButtonCallbackDataDeserializer,
)


def _generate_yt_code():
    characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    return "".join(random.choices(characters, k=11))


def _create_button():
    yt_video_code = _generate_yt_code()
    return YoutubeDownloadAudioButtonBuilder.build(
        button_data=YoutubeDownloadAudioButtonData(),
        callback_data=YoutubeDownloadAudioButtonCallbackData(yt_video_code),
    )


def test_youtube_button_creation():
    _create_button()


def test_callback_deserialization():
    yt_video_code = _generate_yt_code()
    expected_callback_data = YoutubeDownloadAudioButtonCallbackData(yt_video_code)

    btn = YoutubeDownloadAudioButtonBuilder.build(
        button_data=YoutubeDownloadAudioButtonData(),
        callback_data=YoutubeDownloadAudioButtonCallbackData(yt_video_code),
    )

    desirialized_callback_data = (
        YoutubeDownloadAudioButtonCallbackDataDeserializer.deserialize(
            btn.callback_data
        )
    )

    assert expected_callback_data == desirialized_callback_data


def test_not_constant_callback():
    btn1 = _create_button()
    btn2 = _create_button()

    assert btn1.callback_data != btn2.callback_data
