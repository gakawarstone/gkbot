from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ui.buttons.delete_message import deleteMessageButton
from ui.buttons.download import DownloadAction
from ui.buttons.vk import (
    VKDownloadButtonBuilder,
    VKDownloadButtonCallbackData,
)
from utils.vk import VKReference


class VkMarkup:
    @staticmethod
    def get_download_dialog(reference: VKReference) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            VKDownloadButtonBuilder.build(
                VKDownloadButtonCallbackData.from_reference(
                    reference,
                    action=DownloadAction.audio,
                    use_callback_message_as_status=True,
                ),
            ),
            VKDownloadButtonBuilder.build(
                VKDownloadButtonCallbackData.from_reference(
                    reference,
                    action=DownloadAction.video,
                    use_callback_message_as_status=True,
                ),
            ),
            deleteMessageButton,
        )
        return builder.as_markup()
