from typing import Self

from aiogram.types import InlineKeyboardButton
from pydantic import model_validator

from utils.vk import VKReference, VKReferenceKind

from .download import CallbackIdentifier, DownloadAction, DownloadCallbackData

PREFIX = "vk2"


class VKDownloadButtonCallbackData(DownloadCallbackData, prefix=PREFIX, sep="|"):
    reference_kind: VKReferenceKind
    reference_value: CallbackIdentifier

    @model_validator(mode="after")
    def validate_reference(self) -> Self:
        VKReference(self.reference_kind, self.reference_value)
        return self

    @property
    def reference(self) -> VKReference:
        return VKReference(self.reference_kind, self.reference_value)

    @classmethod
    def from_reference(
        cls,
        reference: VKReference,
        *,
        action: DownloadAction,
        use_callback_message_as_status: bool = False,
    ) -> Self:
        return cls(
            action=action,
            use_callback_message_as_status=use_callback_message_as_status,
            reference_kind=reference.kind,
            reference_value=reference.value,
        )


class VKDownloadButtonBuilder:
    @staticmethod
    def build(callback_data: VKDownloadButtonCallbackData) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=callback_data.action.label,
            callback_data=callback_data.pack(),
        )
