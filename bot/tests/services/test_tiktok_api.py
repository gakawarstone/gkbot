from typing import Any

import pytest

from services.tiktok.extractor.api import ApiExtractor


@pytest.mark.parametrize(
    "video",
    [
        {
            "play_addr": {"url_list": ["https://cdn.example/signed-audio"]},
            "width": 0,
            "height": 0,
            "duration": 30000,
        },
        {},
    ],
)
def test_slideshow_uses_images_instead_of_video_play_address(
    video: dict[str, Any],
) -> None:
    info = ApiExtractor._serialize_api_data(
        {
            "data": {
                "image_post_info": {
                    "images": [
                        {"display_image": {"url_list": ["https://cdn.example/1.jpg"]}},
                        {"display_image": {"url_list": ["https://cdn.example/2.jpg"]}},
                    ]
                },
                "video": video,
                "music": {"play_url": {"url_list": ["https://cdn.example/music"]}},
            }
        }
    )

    assert not info.video_url
    assert info.images_urls == [
        "https://cdn.example/1.jpg",
        "https://cdn.example/2.jpg",
    ]
    assert info.music_url == "https://cdn.example/music"
    assert (info.height, info.width, info.duration) == (None, None, None)


def test_video_preserves_play_address_and_metadata() -> None:
    info = ApiExtractor._serialize_api_data(
        {
            "data": {
                "video": {
                    "play_addr": {"url_list": ["https://cdn.example/video.mp4"]},
                    "width": 720,
                    "height": 1280,
                    "duration": 12500,
                },
                "music": {"play_url": {"url_list": ["https://cdn.example/music"]}},
            }
        }
    )

    assert info.video_url == "https://cdn.example/video.mp4"
    assert info.images_urls == []
    assert (info.height, info.width, info.duration) == (1280, 720, 12)
