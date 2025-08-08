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
    def get_download_dialog(url: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            VKDownloadButtonBuilder.build(
                button_data=VKDownloadButtonData.audio,
                callback_data=VKDownloadButtonCallbackData(url=url),
            ),
            VKDownloadButtonBuilder.build(
                button_data=VKDownloadButtonData.video,
                callback_data=VKDownloadButtonCallbackData(url=url),
            ),
            deleteMessageButton,
        )
        return builder.as_markup()
