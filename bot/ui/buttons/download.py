"""Shared types for download callback payloads."""

from enum import StrEnum
from typing import Annotated, Literal

from aiogram.filters.callback_data import CallbackData
from pydantic import BeforeValidator, StringConstraints, field_validator


class DownloadAction(StrEnum):
    audio = "dlmp3"
    video = "dlmp4"

    @property
    def label(self) -> str:
        return "Аудио" if self is DownloadAction.audio else "Видео"

    @property
    def media_type(self) -> Literal["audio", "video"]:
        return "audio" if self is DownloadAction.audio else "video"


def _validate_status(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value in {"0", "1", "False", "True"}:
        return value in {"1", "True"}
    raise ValueError("Status must be a boolean or 0, 1, False, True")


CallbackStatus = Annotated[bool, BeforeValidator(_validate_status)]
CallbackIdentifier = Annotated[str, StringConstraints(min_length=1, pattern=r"^\S+$")]


class DownloadCallbackData(CallbackData, prefix="download"):
    action: DownloadAction
    # Required: a default would make aiogram unpack an empty component as false.
    use_callback_message_as_status: CallbackStatus


class VideoDownloadCallbackData(DownloadCallbackData, prefix="video"):
    @field_validator("action")
    @classmethod
    def validate_video_action(cls, action: DownloadAction) -> DownloadAction:
        if action is not DownloadAction.video:
            raise ValueError("This source only supports video downloads")
        return action
