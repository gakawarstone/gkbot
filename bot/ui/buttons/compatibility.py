"""Read old URL-bearing callbacks while all new buttons use native packing."""

from typing import Any, cast

from aiogram.filters import Filter
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery

from ui.buttons.download import DownloadAction
from ui.buttons.porno365 import Porno365DownloadButtonCallbackData
from ui.buttons.vk import VKDownloadButtonCallbackData
from utils.vk import parse_vk_reference

_LEGACY_PREFIXES: dict[type[CallbackData], str] = {
    VKDownloadButtonCallbackData: "vkbtn:",
    Porno365DownloadButtonCallbackData: "p365btn:",
}


def unpack_callback[T: CallbackData](model: type[T], payload: str) -> T:
    legacy_prefix = _LEGACY_PREFIXES.get(model)
    if legacy_prefix is None or not payload.startswith(legacy_prefix):
        return model.unpack(payload)

    parts = payload.split(":", 3)
    if len(parts) != 4:
        raise ValueError("Legacy callback needs action, status and reference")
    _, raw_action, raw_status, value = parts
    if raw_status not in {"True", "False"}:
        raise ValueError("Legacy status must be True or False")
    action = DownloadAction(raw_action)
    status = raw_status == "True"
    if model is VKDownloadButtonCallbackData:
        return cast(
            T,
            VKDownloadButtonCallbackData.from_reference(
                parse_vk_reference(value),
                action=action,
                use_callback_message_as_status=status,
            ),
        )
    if action is not DownloadAction.video:
        raise ValueError("Porno365 only supports video downloads")
    return cast(
        T,
        Porno365DownloadButtonCallbackData(
            action=DownloadAction.video,
            use_callback_message_as_status=status,
            page_url=value,
        ),
    )


class LegacyDownloadCallbackFilter(Filter):
    def __init__(
        self,
        model: type[VKDownloadButtonCallbackData]
        | type[Porno365DownloadButtonCallbackData],
    ) -> None:
        self.model = model

    async def __call__(self, query: CallbackQuery) -> bool | dict[str, Any]:
        if not query.data or not query.data.startswith(_LEGACY_PREFIXES[self.model]):
            return False
        try:
            data = unpack_callback(self.model, query.data)
        except (TypeError, ValueError):
            return False
        return {"callback_data": data}
