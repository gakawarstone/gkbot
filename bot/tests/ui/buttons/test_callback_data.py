"""Wire-level regression cases, independent of the button implementations."""

from dataclasses import dataclass
from importlib import import_module
from typing import Any

import pytest
from aiogram.filters.callback_data import CallbackData

from ui.buttons.compatibility import unpack_callback
from ui.buttons.download import DownloadAction
from ui.buttons.matreshka import MatreshkaDownloadButtonCallbackData
from ui.buttons.pornhub.download import PornhubDownloadButtonCallbackData
from ui.buttons.porno365 import Porno365DownloadButtonCallbackData
from ui.buttons.sasflix import SasflixDownloadButtonCallbackData
from ui.buttons.vk import VKDownloadButtonCallbackData
from ui.buttons.youtube.download import YoutubeDownloadButtonCallbackData
from ui.keyboards.ytdlp import YtdlpMarkup
from utils.vk import VKReferenceKind


@dataclass(frozen=True)
class CallbackCase:
    model: type[CallbackData]
    fields: dict[str, Any]
    wire: str
    legacy: str
    target_field: str


CASES = [
    CallbackCase(
        YoutubeDownloadButtonCallbackData,
        {
            "action": "dlmp4",
            "use_callback_message_as_status": False,
            "yt_video_code": "000opaque",
        },
        "ytbtn:dlmp4:0:000opaque",
        "ytbtn:dlmp4:False:000opaque",
        "yt_video_code",
    ),
    CallbackCase(
        VKDownloadButtonCallbackData,
        {
            "action": "dlmp4",
            "use_callback_message_as_status": False,
            "reference_kind": "short_url",
            "reference_value": "https://vk.cc/abc?q=a:b",
        },
        "vk2|dlmp4|0|short_url|https://vk.cc/abc?q=a:b",
        "vkbtn:dlmp4:False:https://vk.cc/abc?q=a:b",
        "reference_value",
    ),
    CallbackCase(
        PornhubDownloadButtonCallbackData,
        {
            "action": "dlmp4",
            "use_callback_message_as_status": False,
            "ph_video_code": "ph0001",
        },
        "phbtn:dlmp4:0:ph0001",
        "phbtn:dlmp4:False:ph0001",
        "ph_video_code",
    ),
    CallbackCase(
        Porno365DownloadButtonCallbackData,
        {
            "action": "dlmp4",
            "use_callback_message_as_status": False,
            "page_url": "https://porno365.example:443/video/1?q=a:b",
        },
        "p365v2|dlmp4|0|https://porno365.example:443/video/1?q=a:b",
        "p365btn:dlmp4:False:https://porno365.example:443/video/1?q=a:b",
        "page_url",
    ),
    CallbackCase(
        MatreshkaDownloadButtonCallbackData,
        {"video_id": "000opaque"},
        "matreshkabtn:000opaque",
        "matreshkabtn:000opaque",
        "video_id",
    ),
    CallbackCase(
        SasflixDownloadButtonCallbackData,
        {"topic_uuid": "12345678-1234-5678-1234-567812345678"},
        "sasflixbtn:12345678123456781234567812345678",
        "sasflixbtn:12345678-1234-5678-1234-567812345678",
        "topic_uuid",
    ),
]
DOWNLOAD_CASES = CASES[:4]
URL_CASES = [CASES[1], CASES[3]]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.model.__name__)
def test_native_roundtrip_and_legacy_decode(case: CallbackCase) -> None:
    data = case.model.model_validate(case.fields)
    assert data.pack() == case.wire
    assert case.model.unpack(case.wire) == data
    assert unpack_callback(case.model, case.legacy) == data


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.model.__name__)
@pytest.mark.parametrize("damage", ["prefix", "missing", "extra", "empty"])
def test_malformed_payload(case: CallbackCase, damage: str) -> None:
    sep = case.model.__separator__
    parts = case.wire.split(sep)
    if damage == "prefix":
        parts[0] += "lookalike"
    elif damage == "missing":
        parts.pop()
    elif damage == "extra":
        parts.append("extra")
    else:
        parts[-1] = ""
    with pytest.raises((TypeError, ValueError)):
        case.model.unpack(sep.join(parts))


@pytest.mark.parametrize("case", DOWNLOAD_CASES, ids=lambda case: case.model.__name__)
@pytest.mark.parametrize(
    "token",
    ["", "yes", "no", "on", "off", "true", "false", "2", "-1", " True", "False "],
)
def test_invalid_boolean_wire(case: CallbackCase, token: str) -> None:
    sep = case.model.__separator__
    parts = case.wire.split(sep)
    parts[2] = token
    with pytest.raises(ValueError):
        case.model.unpack(sep.join(parts))


@pytest.mark.parametrize("case", DOWNLOAD_CASES, ids=lambda case: case.model.__name__)
@pytest.mark.parametrize(
    "token, expected", [("0", False), ("1", True), ("False", False), ("True", True)]
)
def test_boolean_wire(case: CallbackCase, token: str, expected: bool) -> None:
    sep = case.model.__separator__
    parts = case.wire.split(sep)
    parts[2] = token
    assert (
        case.model.unpack(sep.join(parts)).model_dump()[
            "use_callback_message_as_status"
        ]
        is expected
    )


@pytest.mark.parametrize("case", DOWNLOAD_CASES, ids=lambda case: case.model.__name__)
def test_unknown_action(case: CallbackCase) -> None:
    fields = {**case.fields, "action": "unknown"}
    with pytest.raises(ValueError):
        case.model.model_validate(fields)


@pytest.mark.parametrize(
    "case", [CASES[2], CASES[3]], ids=lambda case: case.model.__name__
)
def test_audio_rejected_by_video_only_sources(case: CallbackCase) -> None:
    with pytest.raises(ValueError):
        case.model.model_validate({**case.fields, "action": "dlmp3"})


@pytest.mark.parametrize(
    "kind, value",
    [
        ("unknown", "video-123_456"),
        ("short_url", "video-123_456"),
        ("identifier", "https://vk.cc/abc"),
        ("identifier", "invalid"),
    ],
)
def test_invalid_vk_kind_or_reference(kind: str, value: str) -> None:
    with pytest.raises(ValueError):
        VKDownloadButtonCallbackData.model_validate(
            {
                **CASES[1].fields,
                "reference_kind": kind,
                "reference_value": value,
            }
        )


def test_sasflix_rejects_invalid_uuid() -> None:
    with pytest.raises(ValueError):
        SasflixDownloadButtonCallbackData.unpack("sasflixbtn:not-a-uuid")


@pytest.mark.parametrize("case", URL_CASES, ids=lambda case: case.model.__name__)
@pytest.mark.parametrize("status", ["", "yes", "false", "2", "0", "1"])
def test_legacy_url_callbacks_reject_bad_booleans(
    case: CallbackCase, status: str
) -> None:
    parts = case.legacy.split(":", 3)
    parts[2] = status
    with pytest.raises(ValueError):
        unpack_callback(case.model, ":".join(parts))


@pytest.mark.parametrize("case", CASES[:-1], ids=lambda case: case.model.__name__)
def test_outgoing_byte_limit(case: CallbackCase) -> None:
    fields = case.fields.copy()
    fields[case.target_field] = (
        "https://vk.cc/" if case.model is VKDownloadButtonCallbackData else ""
    )
    # Start with a valid value, then fill the exact remaining UTF-8 byte budget.
    fields[case.target_field] += "x"
    overhead = len(case.model.model_validate(fields).pack().encode())
    fields[case.target_field] += "x" * (64 - overhead)
    assert len(case.model.model_validate(fields).pack().encode()) == 64
    fields[case.target_field] += "x"
    with pytest.raises(ValueError, match="too long"):
        case.model.model_validate(fields).pack()


def test_multibyte_limit_and_separator() -> None:
    # Matreshka prefix plus ':' costs 13 bytes; 25 two-byte characters fit.
    data = MatreshkaDownloadButtonCallbackData(video_id="é" * 25)
    assert len(data.pack().encode()) == 63
    with pytest.raises(ValueError, match="too long"):
        MatreshkaDownloadButtonCallbackData(video_id="é" * 26).pack()
    with pytest.raises(ValueError, match="Separator"):
        MatreshkaDownloadButtonCallbackData(video_id="opaque:extra").pack()
    with pytest.raises(ValueError, match="Separator"):
        Porno365DownloadButtonCallbackData(
            action=DownloadAction.video,
            use_callback_message_as_status=False,
            page_url="https://example.com/a|b",
        ).pack()


def test_reference_keeps_kind_and_full_wall_identifier() -> None:
    data = unpack_callback(
        VKDownloadButtonCallbackData, "vkbtn:dlmp4:True:wall-123_456"
    )
    assert data.reference.kind is VKReferenceKind.IDENTIFIER
    assert data.reference.value == "wall-123_456"
    assert data.reference.download_url == "https://vk.com/wall-123_456"


@pytest.mark.parametrize(
    "source, class_name, target",
    [
        ("youtube", "YoutubeFeedItemMarkup", "000opaque"),
        ("vk", "VKFeedVideoItemMarkup", "https://vk.cc/abc"),
        (
            "pornhub",
            "PornhubFeedItemMarkup",
            "https://www.pornhub.com/view_video.php?viewkey=ph0001",
        ),
        ("porno365", "Porno365FeedItemMarkup", "https://porno365.example/v/1?q=a:b"),
        ("matreshka", "MatreshkaFeedItemMarkup", "000opaque"),
        ("sasflix", "SasflixFeedItemMarkup", "12345678-1234-5678-1234-567812345678"),
    ],
)
def test_feed_keyboard_uses_native_payload(
    source: str, class_name: str, target: str
) -> None:
    keyboard = getattr(import_module(f"modules.feed.ui.keyboards.{source}"), class_name)
    case = next(case for case in CASES if source in case.model.__name__.lower())
    markup = keyboard.get_item_markup(42, target)
    actions = []
    for button in markup.inline_keyboard[0]:
        assert button.callback_data is not None
        data = case.model.unpack(button.callback_data)
        assert data.pack() == button.callback_data
        fields = data.model_dump()
        if "action" in fields:
            actions.append(fields["action"])
            assert fields["use_callback_message_as_status"] is False
    if source in {"youtube", "vk"}:
        assert actions == [DownloadAction.audio, DownloadAction.video]
    elif source in {"pornhub", "porno365"}:
        assert actions == [DownloadAction.video]


def test_youtube_dialog_reuses_status() -> None:
    markup = YtdlpMarkup.get_download_dialog("000opaque")
    actions = []
    for button in markup.inline_keyboard[0][:2]:
        assert button.callback_data is not None
        data = YoutubeDownloadButtonCallbackData.unpack(button.callback_data)
        assert data.yt_video_code == "000opaque"
        assert data.use_callback_message_as_status is True
        actions.append(data.action)
    assert actions == [DownloadAction.audio, DownloadAction.video]
