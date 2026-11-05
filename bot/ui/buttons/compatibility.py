"""Read old URL-bearing callbacks while all new buttons use native packing."""

from typing import Any

from aiogram.filters import Filter
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery

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
    fields: dict[str, object] = {
        "action": raw_action,
        "use_callback_message_as_status": raw_status == "True",
    }
    if model is VKDownloadButtonCallbackData:
        reference = parse_vk_reference(value)
        fields.update(reference_kind=reference.kind, reference_value=reference.value)
    else:
        fields["page_url"] = value
    return model.model_validate(fields)


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
