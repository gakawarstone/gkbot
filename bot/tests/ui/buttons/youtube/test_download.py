from . import generate_yt_code

from ui.buttons.youtube.download import (
    YoutubeDownloadButtonBuilder,
    YoutubeDownloadButtonCallbackData,
    YoutubeDownloadButtonCallbackDataDeserializer,
    YoutubeDownloadButtonData,
)


def _create_audio_button():
    yt_video_code = generate_yt_code()
    return YoutubeDownloadButtonBuilder.build(
        button_data=YoutubeDownloadButtonData.audio,
        callback_data=YoutubeDownloadButtonCallbackData(yt_video_code),
    )


def _create_video_button():
    yt_video_code = generate_yt_code()
    return YoutubeDownloadButtonBuilder.build(
        button_data=YoutubeDownloadButtonData.video,
        callback_data=YoutubeDownloadButtonCallbackData(yt_video_code),
    )


def test_youtube_button_creation():
    _create_audio_button()
    _create_video_button()


def test_callback_deserialization():
    yt_video_code = generate_yt_code()
    expected_callback_data = YoutubeDownloadButtonCallbackData(yt_video_code)

    btn = YoutubeDownloadButtonBuilder.build(
        button_data=YoutubeDownloadButtonData.audio,
        callback_data=YoutubeDownloadButtonCallbackData(yt_video_code),
    )

    desirialized_callback_data = (
        YoutubeDownloadButtonCallbackDataDeserializer.deserialize(btn.callback_data)
    )

    assert expected_callback_data == desirialized_callback_data


def test_not_constant_callback():
    btn1 = _create_audio_button()
    btn2 = _create_audio_button()

    assert btn1.callback_data != btn2.callback_data

    btn1 = _create_video_button()
    btn2 = _create_video_button()
    assert btn1.callback_data != btn2.callback_data

    btn1 = _create_audio_button()
    btn2 = _create_video_button()
    assert btn1.callback_data != btn2.callback_data
