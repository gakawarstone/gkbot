from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ui.buttons.vk import (
    VKDownloadButtonBuilder,
    VKDownloadButtonCallbackData,
    VKDownloadButtonData,
)
from ui.buttons.delete_message import deleteMessageButton


class VkMarkup:
    @staticmethod
    def get_download_dialog(vk_id: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            VKDownloadButtonBuilder.build(
                button_data=VKDownloadButtonData.audio,
                callback_data=VKDownloadButtonCallbackData(vk_id, True),
            ),
            VKDownloadButtonBuilder.build(
                button_data=VKDownloadButtonData.video,
                callback_data=VKDownloadButtonCallbackData(vk_id, True),
            ),
            deleteMessageButton,
        )
        return builder.as_markup()
