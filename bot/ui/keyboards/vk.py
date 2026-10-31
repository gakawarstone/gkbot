from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ui.buttons.delete_message import deleteMessageButton
from ui.buttons.vk import (
    VKDownloadButtonBuilder,
    VKDownloadButtonCallbackData,
    VKDownloadButtonData,
)
from utils.vk import VKReference


class VkMarkup:
    @staticmethod
    def get_download_dialog(reference: VKReference) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            VKDownloadButtonBuilder.build(
                button_data=VKDownloadButtonData.audio,
                callback_data=VKDownloadButtonCallbackData(reference, True),
            ),
            VKDownloadButtonBuilder.build(
                button_data=VKDownloadButtonData.video,
                callback_data=VKDownloadButtonCallbackData(reference, True),
            ),
            deleteMessageButton,
        )
        return builder.as_markup()
